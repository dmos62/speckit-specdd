from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from boundary_paths import (
    _ownership_matches,
    _path_entry,
    _resolve_specdd_path,
    normalize_target,
)
from boundary_specdd import _section_body, resolve_target
from boundary_types import BoundaryError, RunCommand
from validation_types import TaskRecord, ValidationError


def _boundary_owners(boundary: Mapping[str, Any]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for item in boundary.get("targets", []):
        if not isinstance(item, Mapping):
            continue
        path = item.get("path")
        authority = item.get("primaryAuthority")
        if isinstance(path, str) and isinstance(authority, str):
            owners[path] = authority
    return owners


def requires_permission_projection(
    boundary: Mapping[str, Any],
    tasks: Sequence[TaskRecord],
) -> bool:
    owners = _boundary_owners(boundary)
    return any(
        task.operation_authority is not None
        and any(
            path in owners and owners[path] != task.operation_authority
            for path in task.targets
        )
        for task in tasks
    )


def _can_modify(
    root: Path,
    spec_path: str,
    spec: Mapping[str, Any],
    target: str,
) -> bool:
    for line in _section_body(spec, "Can modify"):
        candidate = _path_entry(line)
        if candidate is None:
            continue
        try:
            resolved = _resolve_specdd_path(spec_path, candidate)
        except BoundaryError:
            continue
        if _ownership_matches(root, resolved, target):
            return True
    return False


def _authority_context(
    root: Path,
    task: TaskRecord,
    owners: Mapping[str, str],
    executable: str,
    runner: RunCommand,
    cache: dict[str, list[dict[str, Any]]],
) -> dict[str, Mapping[str, Any]]:
    authority = task.operation_authority
    if authority is None:
        return {}

    context_path = next(
        (
            path
            for path in task.targets
            if owners.get(path) == authority
        ),
        authority,
    )
    specs = cache.get(context_path)
    if specs is None:
        target = normalize_target(root, context_path)
        specs, error = resolve_target(
            root,
            target,
            executable,
            runner,
        )
        if error or specs is None:
            raise ValidationError(
                "Could not resolve task SpecDD authority context for "
                f"{authority}: {error or 'unknown resolver error'}"
            )
        cache[context_path] = specs

    context = {
        str(spec["path"]): spec
        for spec in specs
        if isinstance(spec.get("path"), str)
    }
    if authority not in context:
        raise ValidationError(
            "Fresh SpecDD resolution does not include the declared task "
            f"authority {authority}"
        )
    return context


def project_task_modification_permissions(
    root: Path,
    boundary: Mapping[str, Any],
    tasks: Sequence[TaskRecord],
    *,
    executable: str = "specdd",
    runner: RunCommand = subprocess.run,
) -> dict[int, dict[str, dict[str, Any]]]:
    owners = _boundary_owners(boundary)
    resolver_cache: dict[str, list[dict[str, Any]]] = {}
    result: dict[int, dict[str, dict[str, Any]]] = {}

    for task in tasks:
        authority = task.operation_authority
        paths = [path for path in task.targets if path in owners]
        if (
            authority is None
            or not paths
            or all(owners[path] == authority for path in paths)
        ):
            continue

        authority_error: str | None = None
        try:
            context = _authority_context(
                root,
                task,
                owners,
                executable,
                runner,
                resolver_cache,
            )
        except ValidationError as exc:
            context = {}
            authority_error = str(exc)

        task_projection: dict[str, dict[str, Any]] = {}
        for path in paths:
            owner = owners[path]
            allowed = [owner]
            grant_sources: dict[str, list[str]] = {}
            if authority != owner and authority_error is None:
                sources = [
                    spec_path
                    for spec_path, spec in context.items()
                    if _can_modify(root, spec_path, spec, path)
                ]
                if sources:
                    allowed.append(authority)
                    grant_sources[authority] = sources

            projection: dict[str, Any] = {
                "owner": owner,
                "allowedAuthorities": allowed,
                "canModifySources": grant_sources,
            }
            if authority_error is not None:
                projection["authorityResolutionError"] = authority_error
            task_projection[path] = projection
        result[task.order] = task_projection

    return result
