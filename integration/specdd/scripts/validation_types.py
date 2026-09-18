from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class ValidationError(RuntimeError):
    """Feature validation cannot produce a trustworthy result."""


EVOLUTION_CLASSIFICATIONS = (
    "SPEC_EVOLUTION_REQUIRED",
    "AUTHORITY_EVOLUTION_REQUIRED",
)


@dataclass(frozen=True)
class TaskRecord:
    order: int
    task_id: str | None
    story: str | None
    text: str
    targets: tuple[str, ...]
    spec_targets: tuple[str, ...]
    invalid_targets: tuple[str, ...]
    control_targets: tuple[str, ...] = ()
    evolution_markers: tuple[str, ...] = ()
    operation_authority: str | None = None
    invalid_operation_authorities: tuple[str, ...] = ()


def diagnostic(
    code: str,
    severity: str,
    message: str,
    **fields: Any,
) -> dict[str, Any]:
    result = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    result.update(
        {
            key: value
            for key, value in fields.items()
            if value not in (None, [], ())
        }
    )
    return result


def task_fields(task: TaskRecord) -> dict[str, Any]:
    return {
        "taskId": task.task_id,
        "story": task.story,
        "taskOrder": task.order,
        "operationAuthority": task.operation_authority,
    }


def project_boundary_authority(
    boundary: Mapping[str, Any],
    *,
    unresolved_severity: str,
) -> tuple[
    dict[str, str | None],
    dict[str, list[Mapping[str, Any]]],
    list[str],
    list[str],
    list[dict[str, Any]],
]:
    resolved: dict[str, str | None] = {}
    unresolved_by_path: dict[str, list[Mapping[str, Any]]] = {}
    unknown_boundary_paths: list[str] = []
    unresolved_without_path: list[str] = []
    diagnostics: list[dict[str, Any]] = []

    for item in boundary.get("targets", []):
        if not isinstance(item, Mapping):
            continue
        path = item.get("path")
        authority = item.get("primaryAuthority")
        if not isinstance(path, str):
            continue
        resolved[path] = authority if isinstance(authority, str) else None
        if not isinstance(authority, str):
            unknown_boundary_paths.append(path)
            diagnostics.append(
                diagnostic(
                    "UNRESOLVED_TARGET",
                    unresolved_severity,
                    "Resolved boundary target has no primary authority.",
                    targets=[path],
                )
            )

    for item in boundary.get("unresolved", []):
        if not isinstance(item, Mapping):
            continue
        path = item.get("normalizedPath")
        value = item.get("input")
        label = (
            path
            if isinstance(path, str) and path
            else value
            if isinstance(value, str) and value
            else "<unknown>"
        )
        code = item.get("code")
        if isinstance(path, str) and path:
            unresolved_by_path.setdefault(path, []).append(item)
            unknown_boundary_paths.append(path)
        else:
            unresolved_without_path.append(label)
        diagnostics.append(
            diagnostic(
                "UNRESOLVED_TARGET",
                unresolved_severity,
                f"Change Boundary target {label} is unresolved"
                + (f" ({code})." if isinstance(code, str) else "."),
                targets=[label],
                boundaryCode=code if isinstance(code, str) else None,
                candidateAuthorities=item.get("candidateAuthorities"),
            )
        )

    return (
        resolved,
        unresolved_by_path,
        unknown_boundary_paths,
        unresolved_without_path,
        diagnostics,
    )
