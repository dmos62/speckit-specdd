from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from boundary_paths import (
    _ownership_matches,
    _path_entry,
    _resolve_specdd_path,
    normalize_resolver_path,
)
from boundary_runtime import (
    _locate_executable,
    _run,
    normalize_command_output,
)
from boundary_types import BoundaryError, RunCommand, Target


def _section_body(
    spec: Mapping[str, Any],
    name: str,
) -> list[str]:
    sections = spec.get("sections")
    if not isinstance(sections, Mapping):
        return []

    occurrences = sections.get(name)
    if not isinstance(occurrences, list):
        return []

    lines: list[str] = []
    for occurrence in occurrences:
        if not isinstance(occurrence, Mapping):
            continue

        body = occurrence.get("body")
        if isinstance(body, list):
            lines.extend(
                line
                for line in body
                if isinstance(line, str)
            )

    return lines


def extract_resolved_specs(
    payload: Any,
    root: Path,
) -> list[dict[str, Any]]:
    if (
        not isinstance(payload, Mapping)
        or not isinstance(
            payload.get("directories"),
            list,
        )
    ):
        raise BoundaryError(
            "SpecDD resolve JSON is missing the directories array"
        )

    specs: list[dict[str, Any]] = []
    seen: set[str] = set()

    for directory in payload["directories"]:
        if (
            not isinstance(directory, Mapping)
            or not isinstance(
                directory.get("specs"),
                list,
            )
        ):
            raise BoundaryError(
                "SpecDD resolve JSON contains an invalid directory entry"
            )

        for raw_spec in directory["specs"]:
            if (
                not isinstance(raw_spec, Mapping)
                or not isinstance(
                    raw_spec.get("path"),
                    str,
                )
            ):
                raise BoundaryError(
                    "SpecDD resolve JSON contains an invalid spec entry"
                )

            path = normalize_resolver_path(
                root,
                raw_spec["path"],
                spec=True,
            )
            if path in seen:
                continue

            seen.add(path)
            resolved_spec = dict(raw_spec)
            resolved_spec["path"] = path
            specs.append(resolved_spec)

    return specs


def specdd_context_fingerprint(
    specs: Sequence[Mapping[str, Any]],
) -> str:
    projection: list[dict[str, Any]] = []
    for spec in specs:
        path = spec.get("path")
        if not isinstance(path, str) or not path:
            raise BoundaryError(
                "Resolved SpecDD context contains a spec without a path"
            )
        sections = spec.get("sections")
        projection.append(
            {
                "path": path,
                "sections": (
                    sections
                    if isinstance(sections, Mapping)
                    else {}
                ),
            }
        )

    encoded = json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def derive_primary_authority(
    root: Path,
    target: str,
    specs: Sequence[Mapping[str, Any]],
) -> tuple[str | None, list[str]]:
    owners: list[str] = []

    for spec in specs:
        spec_path = str(spec["path"])

        for line in _section_body(
            spec,
            "Owns",
        ):
            candidate = _path_entry(line)
            if candidate is None:
                continue

            try:
                resolved = _resolve_specdd_path(
                    spec_path,
                    candidate,
                )
            except BoundaryError:
                continue

            if _ownership_matches(
                root,
                resolved,
                target,
            ):
                owners.append(spec_path)
                break

    owners = list(dict.fromkeys(owners))
    return (
        owners[0] if len(owners) == 1 else None,
        owners,
    )


def resolve_target(
    root: Path,
    target: Target,
    executable: str,
    runner: RunCommand = subprocess.run,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    command = (
        executable
        if runner is not subprocess.run
        else _locate_executable(executable)
    )

    result = _run(
        [
            command,
            "resolve",
            "--root",
            str(root),
            str(target.absolute_path),
            "--sections",
            "all",
            "--format",
            "json",
        ],
        root,
        runner,
    )

    if result.returncode != 0:
        output = result.stderr or result.stdout or ""
        detail = " ".join(
            normalize_command_output(
                root,
                output,
            ).split()
        )
        reason = (
            "SpecDD resolve exited with status "
            f"{result.returncode}"
        )
        return (
            None,
            f"{reason}: {detail}" if detail else reason,
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return (
            None,
            "SpecDD resolve returned malformed JSON: "
            f"{exc.msg} at line {exc.lineno} "
            f"column {exc.colno}",
        )

    try:
        specs = extract_resolved_specs(
            payload,
            root,
        )
    except BoundaryError as exc:
        return None, str(exc)

    if not specs:
        return (
            None,
            "SpecDD resolve returned no governing specifications",
        )

    return specs, None
