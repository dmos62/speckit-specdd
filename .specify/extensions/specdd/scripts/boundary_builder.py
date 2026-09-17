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
)
from boundary_schema_projection import (
    _generation_metadata,
    _unresolved_record,
)
from boundary_schema_validation import validate_boundary
from boundary_specdd import (
    derive_primary_authority,
    resolve_target,
)
from boundary_types import (
    BoundaryError,
    RunCommand,
    Unresolved,
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
) -> dict[str, Any]:
    if not feature.strip():
        raise BoundaryError(
            "Feature identifier must not be empty"
        )

    normalized = {}
    unresolved: list[Unresolved] = []
    had_input = False

    for raw in raw_targets:
        had_input = True

        try:
            target = normalize_target(
                root,
                raw,
            )
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
            unresolved.append(
                Unresolved(
                    input=raw,
                    code="UNRESOLVED_TARGET",
                    path=target.path,
                    message=(
                        "Target does not exist; SpecDD resolve "
                        "requires existing targets"
                    ),
                )
            )
            continue

        normalized.setdefault(
            target.path,
            target,
        )

    if not had_input:
        raise BoundaryError(
            "At least one target path is required"
        )

    cli_version = (
        cli_version
        or specdd_cli_version(
            root,
            executable,
            runner,
        )
    )
    specdd_framework_version = (
        specdd_framework_version
        or framework_version(root)
    )

    targets: list[dict[str, Any]] = []
    authorities: set[str] = set()

    for path in sorted(normalized):
        target = normalized[path]
        specs, error = resolve_target(
            root,
            target,
            executable,
            runner,
        )

        if error or specs is None:
            unresolved.append(
                Unresolved(
                    input=target.raw,
                    code="RESOLUTION_FAILED",
                    path=target.path,
                    message=(
                        error
                        or "Unknown resolver error"
                    ),
                )
            )
            continue

        authority, owners = derive_primary_authority(
            root,
            target.path,
            specs,
        )

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
                        candidate_authorities=tuple(
                            owners
                        ),
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
        _unresolved_record(
            item,
            schema,
        )
        for item in unresolved
    ]
    unresolved_records.sort(
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            separators=(",", ":"),
        )
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

    validate_boundary(
        result,
        schema,
    )
    return result


def serialize_boundary(
    value: Mapping[str, Any],
) -> str:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
    ) + "\n"


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

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        os.replace(
            temporary,
            output_path,
        )
    finally:
        temporary.unlink(
            missing_ok=True
        )
