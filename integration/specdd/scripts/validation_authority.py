from __future__ import annotations

from typing import Any, Mapping, Sequence

from validation_types import TaskRecord


def project_task_authority(
    task: TaskRecord,
    resolved: Mapping[str, str | None],
    unresolved_by_path: Mapping[str, Sequence[Mapping[str, Any]]],
    represented: set[str],
) -> dict[str, Any]:
    """Project each explicit write to its actual owning authority."""

    groups: dict[str, list[str]] = {}
    unknown: list[str] = []
    missing: list[str] = []

    for path in task.targets:
        if path in resolved:
            authority = resolved[path]
            if authority is None:
                unknown.append(path)
            else:
                groups.setdefault(authority, []).append(path)
        elif path in unresolved_by_path:
            unknown.append(path)
        elif path not in represented:
            missing.append(path)

    authorities = list(groups)
    return {
        "authorities": authorities,
        "authorityGroups": [
            {"authority": authority, "targets": paths}
            for authority, paths in groups.items()
        ],
        "unknown": unknown,
        "missing": missing,
    }
