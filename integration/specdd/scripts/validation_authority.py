from __future__ import annotations

from typing import Any, Mapping, Sequence

from validation_types import TaskRecord


def _permission_record(
    path: str,
    owner: str,
    task_permissions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    raw = task_permissions.get(path, {})
    allowed = []
    if isinstance(raw, Mapping):
        allowed = [
            value
            for value in raw.get("allowedAuthorities", [])
            if isinstance(value, str)
        ]
    if owner not in allowed:
        allowed.append(owner)

    sources = raw.get("canModifySources", {}) if isinstance(raw, Mapping) else {}
    source_projection = {}
    if isinstance(sources, Mapping):
        source_projection = {
            authority: [spec for spec in specs if isinstance(spec, str)]
            for authority, specs in sources.items()
            if isinstance(authority, str) and isinstance(specs, list)
        }

    result: dict[str, Any] = {
        "path": path,
        "owner": owner,
        "allowedAuthorities": allowed,
        "canModifySources": source_projection,
    }
    if isinstance(raw, Mapping):
        authority_error = raw.get("authorityResolutionError")
        if isinstance(authority_error, str) and authority_error:
            result["authorityResolutionError"] = authority_error
    return result


def _operation_authorities(
    task: TaskRecord,
    authorities: Sequence[str],
    permissions: Sequence[Mapping[str, Any]],
) -> list[str]:
    if task.invalid_operation_authorities:
        return []
    declared = task.operation_authority
    if declared is None:
        return list(authorities)
    if permissions and all(
        declared in item.get("allowedAuthorities", [])
        for item in permissions
    ):
        return [declared]
    return []


def project_task_authority(
    task: TaskRecord,
    resolved: Mapping[str, str | None],
    unresolved_by_path: Mapping[str, Sequence[Mapping[str, Any]]],
    represented: set[str],
    task_permissions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    unknown: list[str] = []
    missing: list[str] = []
    permissions: list[dict[str, Any]] = []

    for path in task.targets:
        if path in resolved:
            authority = resolved[path]
            if authority is None:
                unknown.append(path)
            else:
                groups.setdefault(authority, []).append(path)
                permissions.append(
                    _permission_record(path, authority, task_permissions)
                )
        elif path in unresolved_by_path:
            unknown.append(path)
        elif path not in represented:
            missing.append(path)

    authorities = list(groups)
    authority_groups = [
        {"authority": authority, "targets": paths}
        for authority, paths in groups.items()
    ]
    return {
        "authorities": authorities,
        "authorityGroups": authority_groups,
        "declaredOperationAuthority": task.operation_authority,
        "operationAuthorities": _operation_authorities(
            task,
            authorities,
            permissions,
        ),
        "modificationPermissions": permissions,
        "unknown": unknown,
        "missing": missing,
    }
