from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from boundary_types import BoundaryError, RunCommand

FAIL_ON = ("never", "error", "blocking")
_CONTEXT_EVIDENCE_DIRECTORY = Path("specdd") / "boundary-context"


def root_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def serialize_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"


def write_json_output(
    root: Path,
    value: Mapping[str, Any],
    output: str | os.PathLike[str],
) -> None:
    rendered = serialize_json(value)
    if str(output) == "-":
        sys.stdout.write(rendered)
        return

    output_path = root_path(root, str(output))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=output_path.parent,
        prefix=output_path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    try:
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)


def boundary_fingerprint(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_metadata_directory(
    root: Path,
    runner: RunCommand,
) -> Path:
    try:
        result = runner(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise BoundaryError(
            "Required Git executable was not found. Install Git before "
            "refreshing bridge context."
        ) from exc
    except OSError as exc:
        raise BoundaryError(f"Git could not be executed: {exc}") from exc

    if result.returncode != 0 or not result.stdout.strip():
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise BoundaryError(
            "Could not determine the Git metadata directory"
            + (f": {detail}" if detail else "")
        )
    git_dir = Path(result.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return git_dir.resolve(strict=False)


def boundary_context_evidence_path(
    root: Path,
    feature: str,
    runner: RunCommand = subprocess.run,
) -> Path:
    value = feature.strip()
    if not value:
        raise BoundaryError("Feature identifier must not be empty")
    key = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return (
        _git_metadata_directory(root, runner)
        / _CONTEXT_EVIDENCE_DIRECTORY
        / f"{key}.json"
    )


def write_boundary_context_evidence(
    root: Path,
    boundary: Mapping[str, Any],
    context_fingerprints: Mapping[str, str],
    runner: RunCommand = subprocess.run,
) -> Path:
    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise BoundaryError("Change Boundary has no feature identifier")

    target_paths = [
        item["path"]
        for item in boundary.get("targets", [])
        if isinstance(item, Mapping) and isinstance(item.get("path"), str)
    ]
    if set(target_paths) != set(context_fingerprints):
        raise BoundaryError(
            "SpecDD context fingerprints do not match resolved boundary targets"
        )

    document = {
        "schemaVersion": 1,
        "feature": feature,
        "boundarySha256": boundary_fingerprint(boundary),
        "targets": [
            {"path": path, "contextSha256": context_fingerprints[path]}
            for path in sorted(target_paths)
        ],
    }
    output = boundary_context_evidence_path(root, feature, runner)
    write_json_output(root, document, output)
    return output


def load_boundary_context_evidence(
    root: Path,
    boundary: Mapping[str, Any],
    runner: RunCommand = subprocess.run,
) -> dict[str, str]:
    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise BoundaryError("Change Boundary has no feature identifier")

    path = boundary_context_evidence_path(root, feature, runner)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BoundaryError(
            "Change Boundary SpecDD context evidence was not found; "
            "refresh context before authorization"
        ) from exc
    except json.JSONDecodeError as exc:
        raise BoundaryError(
            f"Change Boundary SpecDD context evidence is invalid JSON: {exc}"
        ) from exc

    if not isinstance(value, Mapping) or value.get("schemaVersion") != 1:
        raise BoundaryError(
            "Change Boundary SpecDD context evidence must be a version 1 object"
        )
    if value.get("feature") != feature:
        raise BoundaryError(
            "Change Boundary SpecDD context evidence belongs to another feature"
        )
    if value.get("boundarySha256") != boundary_fingerprint(boundary):
        raise BoundaryError(
            "Change Boundary SpecDD context evidence does not match "
            "the current boundary"
        )

    raw_targets = value.get("targets")
    if not isinstance(raw_targets, list):
        raise BoundaryError(
            "Change Boundary SpecDD context evidence targets must be an array"
        )

    fingerprints: dict[str, str] = {}
    for item in raw_targets:
        if not isinstance(item, Mapping):
            raise BoundaryError(
                "Change Boundary SpecDD context evidence target is invalid"
            )
        target = item.get("path")
        fingerprint = item.get("contextSha256")
        if (
            not isinstance(target, str)
            or not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(char not in "0123456789abcdef" for char in fingerprint)
        ):
            raise BoundaryError(
                "Change Boundary SpecDD context evidence target is invalid"
            )
        if target in fingerprints:
            raise BoundaryError(
                "Change Boundary SpecDD context evidence target is duplicated"
            )
        fingerprints[target] = fingerprint

    expected = {
        item["path"]
        for item in boundary.get("targets", [])
        if isinstance(item, Mapping) and isinstance(item.get("path"), str)
    }
    if set(fingerprints) != expected:
        raise BoundaryError(
            "Change Boundary SpecDD context evidence target set does not "
            "match the current boundary"
        )
    return fingerprints


def result_exit_code(
    result: Mapping[str, Any],
    fail_on: str,
) -> int:
    if fail_on == "never":
        return 0

    summary = result.get("summary", {})
    counts = (
        summary.get("countsBySeverity", {})
        if isinstance(summary, Mapping)
        else {}
    )
    if not isinstance(counts, Mapping):
        return 0
    if fail_on == "blocking":
        return 1 if counts.get("blocking", 0) else 0
    return 1 if counts.get("error", 0) or counts.get("blocking", 0) else 0
