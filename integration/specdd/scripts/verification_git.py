from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from boundary_builder import serialize_boundary, write_boundary
from boundary_paths import normalize_target
from boundary_types import BoundaryError
from verification_types import (
    CONTROL_SELECTION_SOURCES,
    EDITABLE_BOOTSTRAP_CONTROLS,
    LOCAL_BOOTSTRAP_CONTROL,
    ChangeSet,
    GitChange,
    VerificationError,
)

RunGit = Callable[..., subprocess.CompletedProcess[str]]

_GENERATED_PREFIXES = (".specify/", ".specify-agent/")
_GENERATED_EXACT = {LOCAL_BOOTSTRAP_CONTROL}
_AUTHORIZATION_SNAPSHOT_RELATIVE = Path("specdd") / "authorization-boundary.json"
_AUTHORIZATION_SPEC_PLAN_RELATIVE = Path("specdd") / "authorization-spec-evolution.json"


def _run_git(
    root: Path,
    args: Sequence[str],
    runner: RunGit,
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            ["git", *args],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise VerificationError(
            "Required Git executable was not found. Install Git and run "
            "`bash scripts/bootstrap.sh --check` before verification."
        ) from exc
    except OSError as exc:
        raise VerificationError(f"Git could not be executed: {exc}") from exc


def _metadata_path(root: Path, relative: Path, runner: RunGit) -> Path:
    result = _run_git(root, ["rev-parse", "--git-dir"], runner)
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise VerificationError(
            "Could not determine the Git metadata directory"
            + (f": {detail}" if detail else "")
        )
    raw_git_dir = result.stdout.strip()
    if not raw_git_dir:
        raise VerificationError("Git returned an empty metadata directory")
    git_dir = Path(raw_git_dir)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return git_dir.resolve(strict=False) / relative


def authorization_snapshot_path(
    root: Path,
    *,
    runner: RunGit = subprocess.run,
) -> Path:
    return _metadata_path(root, _AUTHORIZATION_SNAPSHOT_RELATIVE, runner)


def authorization_spec_plan_path(
    root: Path,
    *,
    runner: RunGit = subprocess.run,
) -> Path:
    return _metadata_path(root, _AUTHORIZATION_SPEC_PLAN_RELATIVE, runner)


def _boundary_fingerprint(boundary: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        serialize_boundary(boundary).encode("utf-8")
    ).hexdigest()


def _spec_plan_document(
    boundary: Mapping[str, Any],
    targets: Sequence[str],
    control_selections: Mapping[str, str],
) -> dict[str, Any]:
    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise VerificationError("Authorization boundary has no feature identifier")
    return {
        "schemaVersion": 1,
        "feature": feature,
        "boundarySha256": _boundary_fingerprint(boundary),
        "targets": sorted(dict.fromkeys(targets)),
        "controlTargets": [
            {"path": path, "selectedBy": source}
            for path, source in sorted(control_selections.items())
        ],
    }


def write_authorization_evidence(
    root: Path,
    boundary: Mapping[str, Any],
    spec_targets: Sequence[str],
    *,
    control_selections: Mapping[str, str] | None = None,
    runner: RunGit = subprocess.run,
) -> tuple[Path, Path]:
    plan_path = authorization_spec_plan_path(root, runner=runner)
    snapshot_path = authorization_snapshot_path(root, runner=runner)
    write_boundary(
        _spec_plan_document(
            boundary,
            spec_targets,
            control_selections or {},
        ),
        plan_path,
    )
    write_boundary(boundary, snapshot_path)
    return snapshot_path, plan_path


def load_authorization_plan(
    root: Path,
    path: Path,
    boundary: Mapping[str, Any],
) -> tuple[tuple[str, ...], dict[str, str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(
            "Authorization specification plan was not found: "
            f"{path}. Run authorization again before verification."
        ) from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(
            f"Authorization specification plan is invalid JSON: {path}: {exc}"
        ) from exc

    if not isinstance(value, Mapping) or value.get("schemaVersion") != 1:
        raise VerificationError(
            "Authorization specification plan must be a version 1 object"
        )
    if value.get("feature") != boundary.get("feature"):
        raise VerificationError(
            "Authorization specification plan belongs to a different feature"
        )
    if value.get("boundarySha256") != _boundary_fingerprint(boundary):
        raise VerificationError(
            "Authorization specification plan does not match the boundary snapshot"
        )

    raw_targets = value.get("targets")
    if not isinstance(raw_targets, list) or any(
        not isinstance(item, str) for item in raw_targets
    ):
        raise VerificationError(
            "Authorization specification plan targets must be a string array"
        )
    if len(raw_targets) != len(set(raw_targets)):
        raise VerificationError(
            "Authorization specification plan targets must be unique"
        )

    targets: list[str] = []
    for raw in raw_targets:
        if not raw.lower().endswith(".sdd"):
            raise VerificationError(
                f"Authorization specification plan target is not an .sdd file: {raw}"
            )
        try:
            normalized = normalize_target(root, raw).path
        except BoundaryError as exc:
            raise VerificationError(
                f"Authorization specification plan target is invalid: {raw}: {exc}"
            ) from exc
        if normalized != raw:
            raise VerificationError(
                "Authorization specification plan target is not canonical: " + raw
            )
        targets.append(raw)

    raw_controls = value.get("controlTargets", [])
    if not isinstance(raw_controls, list):
        raise VerificationError(
            "Authorization control selections must be an array"
        )
    controls: dict[str, str] = {}
    for item in raw_controls:
        if not isinstance(item, Mapping):
            raise VerificationError(
                "Authorization control selection must be an object"
            )
        path = item.get("path")
        source = item.get("selectedBy")
        if path not in EDITABLE_BOOTSTRAP_CONTROLS:
            raise VerificationError(
                f"Authorization control selection is not editable: {path}"
            )
        if source not in CONTROL_SELECTION_SOURCES:
            raise VerificationError(
                f"Authorization control selection has invalid source: {source}"
            )
        if path in controls:
            raise VerificationError(
                f"Authorization control selection is duplicated: {path}"
            )
        controls[str(path)] = str(source)
    return tuple(targets), controls


def _status_name(value: str) -> str:
    if value == "??":
        return "UNTRACKED"
    if "D" in value:
        return "DELETED"
    if "A" in value:
        return "ADDED"
    if "M" in value:
        return "MODIFIED"
    return "CHANGED"


def _inside(path: str, directory: str | None) -> bool:
    return bool(
        directory
        and (path == directory or path.startswith(directory.rstrip("/") + "/"))
    )


def _feature_path(root: Path, feature_dir: str | Path | None) -> str | None:
    if feature_dir is None:
        return None
    try:
        return normalize_target(root, str(feature_dir)).path
    except BoundaryError as exc:
        raise VerificationError(
            f"Active feature directory is invalid: {feature_dir}: {exc}"
        ) from exc


def _category(path: str, feature_dir: str | None) -> str:
    if _inside(path, feature_dir):
        return "feature"
    if path in _GENERATED_EXACT or any(
        path.startswith(prefix) for prefix in _GENERATED_PREFIXES
    ):
        return "generated"
    if path.startswith(".specdd/"):
        return "control"
    if path.lower().endswith(".sdd"):
        return "spec"
    return "write"


def collect_git_changes(
    root: Path,
    *,
    feature_dir: str | Path | None = None,
    runner: RunGit = subprocess.run,
) -> ChangeSet:
    result = _run_git(
        root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"],
        runner,
    )
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise VerificationError(
            "Could not determine changed paths from Git"
            + (f": {detail}" if detail else "")
        )

    feature_path = _feature_path(root, feature_dir)
    groups: dict[str, list[GitChange]] = {
        "write": [],
        "spec": [],
        "control": [],
        "feature": [],
        "generated": [],
    }
    for record in result.stdout.split("\0"):
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise VerificationError(
                "Git returned an unexpected porcelain status record"
            )
        raw_path = record[3:]
        try:
            target = normalize_target(root, raw_path)
        except BoundaryError as exc:
            raise VerificationError(
                f"Git returned an invalid repository path: {raw_path}: {exc}"
            ) from exc
        groups[_category(target.path, feature_path)].append(
            GitChange(
                path=target.path,
                status=_status_name(record[:2]),
                deleted=not target.absolute_path.exists(),
            )
        )

    for values in groups.values():
        values.sort(key=lambda item: item.path)
    return ChangeSet(
        writes=tuple(groups["write"]),
        specs=tuple(groups["spec"]),
        controls=tuple(groups["control"]),
        feature_artifacts=tuple(groups["feature"]),
        generated=tuple(groups["generated"]),
    )
