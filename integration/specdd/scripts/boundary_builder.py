from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from boundary_paths import normalize_target
from boundary_runtime import framework_version, specdd_cli_version
from boundary_schema_projection import _generation_metadata, _unresolved_record
from boundary_schema_validation import validate_boundary
from boundary_specdd import (
    derive_primary_authority,
    resolve_target,
    specdd_context_fingerprint,
)
from boundary_types import BoundaryError, RunCommand, Unresolved

_CONTEXT_EVIDENCE_DIRECTORY = Path("specdd") / "boundary-context"


def build_change_boundary(
    root: Path,
    raw_targets: Iterable[str],
    *,
    feature: str,
    schema: Mapping[str, Any],
    executable: str = "specdd",
    runner: RunCommand = subprocess.run,
    cli_version: str | None = None,
    specdd_framework_version: str | None = None,
    context_fingerprints: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not feature.strip():
        raise BoundaryError("Feature identifier must not be empty")
    if context_fingerprints is not None:
        context_fingerprints.clear()

    normalized = {}
    missing = []
    unresolved: list[Unresolved] = []
    had_input = False

    for raw in raw_targets:
        had_input = True
        try:
            target = normalize_target(root, raw)
        except BoundaryError as exc:
            unresolved.append(
                Unresolved(
                    input=raw or "<empty>",
                    code="INVALID_TARGET",
                    message=str(exc),
                )
            )
            continue
        if not target.absolute_path.exists():
            missing.append(target)
            continue
        normalized.setdefault(target.path, target)

    if not had_input:
        raise BoundaryError("At least one target path is required")

    cli_version = cli_version or specdd_cli_version(root, executable, runner)
    specdd_framework_version = (
        specdd_framework_version or framework_version(root)
    )
    for target in missing:
        unresolved.append(
            Unresolved(
                input=target.raw,
                code="UNRESOLVED_TARGET",
                path=target.path,
                message=(
                    "INTENDED_TARGET_UNSUPPORTED: SpecDD CLI "
                    f"{cli_version} requires resolve targets to exist; "
                    "the bridge will not infer pre-creation authority."
                ),
            )
        )

    targets: list[dict[str, Any]] = []
    authorities: set[str] = set()
    for path in sorted(normalized):
        target = normalized[path]
        specs, error = resolve_target(root, target, executable, runner)
        if error or specs is None:
            unresolved.append(
                Unresolved(
                    input=target.raw,
                    code="RESOLUTION_FAILED",
                    path=target.path,
                    message=error or "Unknown resolver error",
                )
            )
            continue

        authority, owners = derive_primary_authority(root, target.path, specs)
        if authority is None:
            if owners:
                unresolved.append(
                    Unresolved(
                        input=target.raw,
                        code="AMBIGUOUS_AUTHORITY",
                        path=target.path,
                        message=(
                            "Multiple SpecDD specs claim ownership: "
                            + ", ".join(owners)
                        ),
                        candidate_authorities=tuple(owners),
                    )
                )
            else:
                unresolved.append(
                    Unresolved(
                        input=target.raw,
                        code="UNRESOLVED_TARGET",
                        path=target.path,
                        message=(
                            "No primary authority could be derived "
                            "from resolved Owns entries"
                        ),
                    )
                )
            continue

        authorities.add(authority)
        if context_fingerprints is not None:
            context_fingerprints[target.path] = specdd_context_fingerprint(specs)
        targets.append(
            {
                "path": target.path,
                "primaryAuthority": authority,
                "resolvedSpecs": [
                    str(resolved_spec["path"])
                    for resolved_spec in specs
                ],
            }
        )

    unresolved_records = [
        _unresolved_record(item, schema)
        for item in unresolved
    ]
    unresolved_records.sort(
        key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"))
    )
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "feature": feature.strip(),
        "targets": targets,
        "authorities": sorted(authorities),
        "crossBoundary": len(authorities) > 1,
        "unresolved": unresolved_records,
    }

    generation = _generation_metadata(
        schema,
        cli_version,
        specdd_framework_version,
    )
    if generation is not None:
        result[generation[0]] = generation[1]

    validate_boundary(result, schema)
    return result


def serialize_boundary(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def boundary_fingerprint(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_boundary(
    value: Mapping[str, Any],
    output: str | os.PathLike[str] | None,
) -> None:
    rendered = serialize_boundary(value)
    if output is None or str(output) == "-":
        sys.stdout.write(rendered)
        return

    output_path = Path(output).expanduser()
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
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


def _git_metadata_directory(root: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise BoundaryError(
            "Required Git executable was not found. Install Git and run "
            "`bash scripts/bootstrap.sh --check` before refreshing context."
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
) -> Path:
    value = feature.strip()
    if not value:
        raise BoundaryError("Feature identifier must not be empty")
    key = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return (
        _git_metadata_directory(root)
        / _CONTEXT_EVIDENCE_DIRECTORY
        / f"{key}.json"
    )


def write_boundary_context_evidence(
    root: Path,
    boundary: Mapping[str, Any],
    context_fingerprints: Mapping[str, str],
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
            {
                "path": path,
                "contextSha256": context_fingerprints[path],
            }
            for path in sorted(target_paths)
        ],
    }
    output = boundary_context_evidence_path(root, feature)
    write_boundary(document, output)
    return output


def load_boundary_context_evidence(
    root: Path,
    boundary: Mapping[str, Any],
) -> dict[str, str]:
    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise BoundaryError("Change Boundary has no feature identifier")

    path = boundary_context_evidence_path(root, feature)
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
            or any(
                character not in "0123456789abcdef"
                for character in fingerprint
            )
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
