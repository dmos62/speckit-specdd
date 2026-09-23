from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from boundary_paths import normalize_target
from boundary_runtime import (
    framework_version,
    specdd_cli_version,
    specdd_resolve_supports_intended_targets,
)
from boundary_schema_projection import _generation_metadata, _unresolved_record
from boundary_schema_validation import validate_boundary
from boundary_specdd import (
    derive_primary_authority,
    resolve_target,
    specdd_context_fingerprint,
)
from boundary_types import BoundaryError, RunCommand, Unresolved
from cli_output import (
    _git_metadata_directory as _cli_git_metadata_directory,
    boundary_context_evidence_path as _boundary_context_evidence_path,
    boundary_fingerprint,
    load_boundary_context_evidence as _load_boundary_context_evidence,
    write_boundary_context_evidence as _write_boundary_context_evidence,
)


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
    intended_targets_supported: bool | None = None,
) -> dict[str, Any]:
    if not feature.strip():
        raise BoundaryError("Feature identifier must not be empty")
    if context_fingerprints is not None:
        context_fingerprints.clear()

    normalized = {}
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
        normalized.setdefault(target.path, target)

    if not had_input:
        raise BoundaryError("At least one target path is required")

    cli_version = cli_version or specdd_cli_version(root, executable, runner)
    specdd_framework_version = (
        specdd_framework_version or framework_version(root)
    )
    has_missing = any(
        not target.absolute_path.exists() for target in normalized.values()
    )
    if intended_targets_supported is None and has_missing:
        intended_targets_supported = specdd_resolve_supports_intended_targets(
            root,
            executable,
            runner,
        )

    targets: list[dict[str, Any]] = []
    authorities: set[str] = set()
    for path in sorted(normalized):
        target = normalized[path]
        if (
            not target.absolute_path.exists()
            and intended_targets_supported is not True
        ):
            unresolved.append(
                Unresolved(
                    input=target.raw,
                    code="INTENDED_TARGET_UNSUPPORTED",
                    path=target.path,
                    message=(
                        f"SpecDD CLI {cli_version} does not expose complete "
                        "typed intended-target resolution; the bridge will not "
                        "infer pre-creation authority."
                    ),
                )
            )
            continue

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

    unresolved_records = [_unresolved_record(item, schema) for item in unresolved]
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
    return _cli_git_metadata_directory(root, subprocess.run)


def boundary_context_evidence_path(root: Path, feature: str) -> Path:
    return _boundary_context_evidence_path(root, feature, subprocess.run)


def write_boundary_context_evidence(
    root: Path,
    boundary: Mapping[str, Any],
    context_fingerprints: Mapping[str, str],
) -> Path:
    return _write_boundary_context_evidence(
        root,
        boundary,
        context_fingerprints,
        subprocess.run,
    )


def load_boundary_context_evidence(
    root: Path,
    boundary: Mapping[str, Any],
) -> dict[str, str]:
    return _load_boundary_context_evidence(root, boundary, subprocess.run)
