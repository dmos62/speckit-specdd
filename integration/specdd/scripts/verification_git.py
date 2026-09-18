from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from boundary_builder import serialize_boundary, write_boundary
from boundary_paths import normalize_target
from boundary_types import BoundaryError
from verification_types import (
    CONTROL_SELECTION_SOURCES,
    EDITABLE_BOOTSTRAP_CONTROLS,
    ChangeSet,
    GitChange,
    VerificationError,
    is_generated_path,
)

RunGit = Callable[..., subprocess.CompletedProcess[str]]
_METADATA_ROOT = Path("specdd")
_AUTHORIZATION_SNAPSHOT = _METADATA_ROOT / "authorization-boundary.json"
_AUTHORIZATION_PLAN = _METADATA_ROOT / "authorization-spec-evolution.json"
_AUTHORIZATION_BASELINE = _METADATA_ROOT / "authorization-git-baseline.json"
def _run_git(root: Path, args: Sequence[str], runner: RunGit) -> subprocess.CompletedProcess[str]:
    try:
        return runner(["git", *args], cwd=str(root), check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise VerificationError(
            "Required Git executable was not found. Install Git and run "
            "`bash scripts/bootstrap.sh --check` before verification."
        ) from exc
    except OSError as exc:
        raise VerificationError(f"Git could not be executed: {exc}") from exc
def _metadata_path(root: Path, relative: Path, runner: RunGit) -> Path:
    result = _run_git(root, ["rev-parse", "--git-dir"], runner)
    if result.returncode != 0 or not result.stdout.strip():
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise VerificationError("Could not determine the Git metadata directory" + (f": {detail}" if detail else ""))
    git_dir = Path(result.stdout.strip())
    return (git_dir if git_dir.is_absolute() else root / git_dir).resolve(strict=False) / relative
def authorization_snapshot_path(root: Path, *, runner: RunGit = subprocess.run) -> Path:
    return _metadata_path(root, _AUTHORIZATION_SNAPSHOT, runner)
def authorization_spec_plan_path(root: Path, *, runner: RunGit = subprocess.run) -> Path:
    return _metadata_path(root, _AUTHORIZATION_PLAN, runner)
def authorization_git_baseline_path(root: Path, *, runner: RunGit = subprocess.run) -> Path:
    return _metadata_path(root, _AUTHORIZATION_BASELINE, runner)
def _boundary_fingerprint(boundary: Mapping[str, Any]) -> str:
    return hashlib.sha256(serialize_boundary(boundary).encode("utf-8")).hexdigest()
def _git_head(root: Path, runner: RunGit) -> str | None:
    result = _run_git(root, ["rev-parse", "--verify", "--quiet", "HEAD"], runner)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    if result.returncode == 1 and not (result.stderr or result.stdout).strip():
        return None
    detail = " ".join((result.stderr or result.stdout or "").split())
    raise VerificationError("Could not determine the authorization-time Git HEAD" + (f": {detail}" if detail else ""))
def _path_state(root: Path, path: str) -> str:
    absolute = root.joinpath(*Path(path).parts)
    if not os.path.lexists(absolute):
        return "missing"
    if absolute.is_symlink():
        payload = os.readlink(absolute).encode("utf-8", errors="surrogateescape")
        kind = "symlink"
    elif absolute.is_file():
        payload, kind = absolute.read_bytes(), "file"
    else:
        raise VerificationError(f"Git change path is not a file or symlink: {path}")
    return f"{kind}:" + hashlib.sha256(payload).hexdigest()
def _status_name(value: str) -> str:
    if value == "??":
        return "UNTRACKED"
    if "D" in value:
        return "DELETED"
    if "A" in value:
        return "ADDED"
    return "MODIFIED" if "M" in value else "CHANGED"
def _git_changes(root: Path, runner: RunGit) -> list[GitChange]:
    result = _run_git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"], runner)
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise VerificationError("Could not determine changed paths from Git" + (f": {detail}" if detail else ""))
    changes = []
    for record in result.stdout.split("\0"):
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise VerificationError("Git returned an unexpected porcelain status record")
        try:
            target = normalize_target(root, record[3:])
        except BoundaryError as exc:
            raise VerificationError(f"Git returned an invalid repository path: {record[3:]}: {exc}") from exc
        changes.append(GitChange(target.path, _status_name(record[:2]), not os.path.lexists(target.absolute_path)))
    return sorted(changes, key=lambda item: item.path)
def _spec_plan_document(boundary: Mapping[str, Any], targets: Sequence[str], controls: Mapping[str, str]) -> dict[str, Any]:
    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise VerificationError("Authorization boundary has no feature identifier")
    return {
        "schemaVersion": 1,
        "feature": feature,
        "boundarySha256": _boundary_fingerprint(boundary),
        "targets": sorted(dict.fromkeys(targets)),
        "controlTargets": [{"path": path, "selectedBy": source} for path, source in sorted(controls.items())],
    }
def _git_baseline_document(root: Path, boundary: Mapping[str, Any], runner: RunGit) -> dict[str, Any]:
    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise VerificationError("Authorization boundary has no feature identifier")
    return {
        "schemaVersion": 1,
        "feature": feature,
        "boundarySha256": _boundary_fingerprint(boundary),
        "head": _git_head(root, runner),
        "entries": [{"path": item.path, "state": _path_state(root, item.path)} for item in _git_changes(root, runner)],
    }

def write_authorization_evidence(
    root: Path, boundary: Mapping[str, Any], spec_targets: Sequence[str], *,
    control_selections: Mapping[str, str] | None = None, runner: RunGit = subprocess.run,
) -> tuple[Path, Path]:
    baseline = _git_baseline_document(root, boundary, runner)
    plan_path = authorization_spec_plan_path(root, runner=runner)
    baseline_path = authorization_git_baseline_path(root, runner=runner)
    snapshot_path = authorization_snapshot_path(root, runner=runner)
    write_boundary(_spec_plan_document(boundary, spec_targets, control_selections or {}), plan_path)
    write_boundary(baseline, baseline_path)
    write_boundary(boundary, snapshot_path)
    return snapshot_path, plan_path

def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(f"{label} was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"{label} is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, Mapping) or value.get("schemaVersion") != 1:
        raise VerificationError(f"{label} must be a version 1 object")
    return value

def _matches_boundary(value: Mapping[str, Any], boundary: Mapping[str, Any], label: str) -> None:
    if value.get("feature") != boundary.get("feature") or value.get("boundarySha256") != _boundary_fingerprint(boundary):
        raise VerificationError(f"{label} does not match the boundary snapshot")

def load_authorization_plan(root: Path, path: Path, boundary: Mapping[str, Any]) -> tuple[tuple[str, ...], dict[str, str]]:
    value = _load_json(path, "Authorization specification plan")
    _matches_boundary(value, boundary, "Authorization specification plan")
    raw_targets = value.get("targets")
    if not isinstance(raw_targets, list) or any(not isinstance(item, str) for item in raw_targets) or len(raw_targets) != len(set(raw_targets)):
        raise VerificationError("Authorization specification plan targets must be a unique string array")
    targets = []
    for raw in raw_targets:
        if not raw.lower().endswith(".sdd"):
            raise VerificationError(f"Authorization specification plan target is not an .sdd file: {raw}")
        try:
            normalized = normalize_target(root, raw).path
        except BoundaryError as exc:
            raise VerificationError(f"Authorization specification plan target is invalid: {raw}: {exc}") from exc
        if normalized != raw:
            raise VerificationError("Authorization specification plan target is not canonical: " + raw)
        targets.append(raw)
    raw_controls, controls = value.get("controlTargets", []), {}
    if not isinstance(raw_controls, list):
        raise VerificationError("Authorization control selections must be an array")
    for item in raw_controls:
        if not isinstance(item, Mapping):
            raise VerificationError("Authorization control selection must be an object")
        path, source = item.get("path"), item.get("selectedBy")
        if path not in EDITABLE_BOOTSTRAP_CONTROLS:
            raise VerificationError(f"Authorization control selection is not editable: {path}")
        if source not in CONTROL_SELECTION_SOURCES:
            raise VerificationError(f"Authorization control selection has invalid source: {source}")
        if path in controls:
            raise VerificationError(f"Authorization control selection is duplicated: {path}")
        controls[str(path)] = str(source)
    return tuple(targets), controls

def load_authorization_git_baseline(root: Path, path: Path, boundary: Mapping[str, Any]) -> dict[str, Any]:
    value = _load_json(path, "Authorization Git baseline")
    _matches_boundary(value, boundary, "Authorization Git baseline")
    head, raw_entries = value.get("head"), value.get("entries")
    if head is not None and (not isinstance(head, str) or not head):
        raise VerificationError("Authorization Git baseline HEAD is invalid")
    if not isinstance(raw_entries, list):
        raise VerificationError("Authorization Git baseline entries must be an array")
    entries: dict[str, str] = {}
    for item in raw_entries:
        if not isinstance(item, Mapping):
            raise VerificationError("Authorization Git baseline entry must be an object")
        path, state = item.get("path"), item.get("state")
        if not isinstance(path, str) or not isinstance(state, str):
            raise VerificationError("Authorization Git baseline entry is invalid")
        try:
            normalized = normalize_target(root, path).path
        except BoundaryError as exc:
            raise VerificationError(f"Authorization Git baseline path is invalid: {path}: {exc}") from exc
        if normalized != path or path in entries or (state != "missing" and not state.startswith(("file:", "symlink:"))):
            raise VerificationError(f"Authorization Git baseline entry is invalid: {path}")
        entries[path] = state
    return {"head": head, "entries": entries}

def _inside(path: str, directory: str | None) -> bool:
    return bool(directory and (path == directory or path.startswith(directory.rstrip("/") + "/")))

def _category(path: str, feature_dir: str | None) -> str:
    if _inside(path, feature_dir):
        return "feature"
    if is_generated_path(path):
        return "generated"
    if path.startswith(".specdd/"):
        return "control"
    return "spec" if path.lower().endswith(".sdd") else "write"

def collect_git_changes(
    root: Path, *, feature_dir: str | Path | None = None,
    baseline: Mapping[str, Any] | None = None, runner: RunGit = subprocess.run,
) -> ChangeSet:
    try:
        feature_path = normalize_target(root, str(feature_dir)).path if feature_dir is not None else None
    except BoundaryError as exc:
        raise VerificationError(f"Active feature directory is invalid: {feature_dir}: {exc}") from exc
    baseline_entries = baseline.get("entries", {}) if baseline else {}
    if baseline and _git_head(root, runner) != baseline.get("head"):
        raise VerificationError(
            "Git HEAD changed after authorization; the operation baseline cannot be compared safely. "
            "Start a fresh authorization from the current repository state."
        )
    groups: dict[str, list[GitChange]] = {name: [] for name in ("write", "spec", "control", "feature", "generated", "preauthorization")}
    current = _git_changes(root, runner)
    current_paths = {item.path for item in current}
    for item in current:
        if item.path in baseline_entries and _path_state(root, item.path) == baseline_entries[item.path]:
            groups["preauthorization"].append(item)
        else:
            groups[_category(item.path, feature_path)].append(item)
    for path, state in baseline_entries.items():
        current_state = _path_state(root, path)
        if path not in current_paths and current_state != state:
            item = GitChange(path, "CHANGED_SINCE_AUTHORIZATION", current_state == "missing")
            groups[_category(path, feature_path)].append(item)
    for values in groups.values():
        values.sort(key=lambda item: item.path)
    return ChangeSet(
        writes=tuple(groups["write"]), specs=tuple(groups["spec"]), controls=tuple(groups["control"]),
        feature_artifacts=tuple(groups["feature"]), generated=tuple(groups["generated"]),
        preauthorization=tuple(groups["preauthorization"]),
    )
