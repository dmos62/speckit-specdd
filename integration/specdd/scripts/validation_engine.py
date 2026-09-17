from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from validation_types import TaskRecord, ValidationError

VALID_STAGES = {
    "planning",
    "tasks",
    "implementation",
}
SEVERITIES = (
    "info",
    "warning",
    "error",
    "blocking",
)


def _scope_severity(
    stage: str,
) -> str:
    return {
        "planning": "warning",
        "tasks": "error",
        "implementation": "blocking",
    }[stage]


def _unresolved_severity(
    stage: str,
) -> str:
    return {
        "planning": "warning",
        "tasks": "error",
        "implementation": "error",
    }[stage]


def _diagnostic(
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


def _task_fields(
    task: TaskRecord,
) -> dict[str, Any]:
    return {
        "taskId": task.task_id,
        "story": task.story,
        "taskOrder": task.order,
    }


def _unresolved_label(
    item: Mapping[str, Any],
) -> str:
    path = item.get("normalizedPath")
    if isinstance(path, str) and path:
        return path

    value = item.get("input")
    if isinstance(value, str) and value:
        return value

    return "<unknown>"


def validate_feature(
    boundary: Mapping[str, Any],
    tasks: Sequence[TaskRecord],
    *,
    stage: str,
    expected_feature: str | None = None,
) -> dict[str, Any]:
    if stage not in VALID_STAGES:
        raise ValidationError(
            "Validation stage must be one of: "
            + ", ".join(sorted(VALID_STAGES))
        )

    diagnostics: list[dict[str, Any]] = []

    feature = boundary.get("feature")
    if not isinstance(feature, str) or not feature:
        raise ValidationError(
            "Change Boundary does not contain a feature identifier"
        )

    if (
        expected_feature is not None
        and feature != expected_feature
    ):
        diagnostics.append(
            _diagnostic(
                "STALE_BOUNDARY",
                _scope_severity(stage),
                (
                    "Change Boundary feature does not match the "
                    "active feature."
                ),
                expectedFeature=expected_feature,
                boundaryFeature=feature,
            )
        )

    resolved: dict[str, str | None] = {}
    unknown_boundary_paths: list[str] = []

    for item in boundary.get("targets", []):
        if not isinstance(item, Mapping):
            continue

        path = item.get("path")
        authority = item.get("primaryAuthority")
        if not isinstance(path, str):
            continue

        resolved[path] = (
            authority
            if isinstance(authority, str)
            else None
        )

        if not isinstance(authority, str):
            unknown_boundary_paths.append(path)
            diagnostics.append(
                _diagnostic(
                    "UNRESOLVED_TARGET",
                    _unresolved_severity(stage),
                    (
                        "Resolved boundary target has no "
                        "determinable primary authority."
                    ),
                    targets=[path],
                )
            )

    unresolved_by_path: dict[
        str,
        list[Mapping[str, Any]],
    ] = {}
    unresolved_without_path: list[str] = []

    for item in boundary.get("unresolved", []):
        if not isinstance(item, Mapping):
            continue

        label = _unresolved_label(item)
        path = item.get("normalizedPath")
        code = item.get("code")

        if isinstance(path, str) and path:
            unresolved_by_path.setdefault(
                path,
                [],
            ).append(item)
            unknown_boundary_paths.append(path)
        else:
            unresolved_without_path.append(label)

        diagnostics.append(
            _diagnostic(
                "UNRESOLVED_TARGET",
                _unresolved_severity(stage),
                (
                    f"Change Boundary target {label} is unresolved"
                    + (
                        f" ({code})."
                        if isinstance(code, str)
                        else "."
                    )
                ),
                targets=[label],
                boundaryCode=(
                    code
                    if isinstance(code, str)
                    else None
                ),
                candidateAuthorities=item.get(
                    "candidateAuthorities"
                ),
            )
        )

    represented = (
        set(resolved)
        | set(unresolved_by_path)
    )
    task_results: list[dict[str, Any]] = []

    for task in tasks:
        groups: dict[str, list[str]] = {}
        unknown: list[str] = []
        missing: list[str] = []

        for path in task.targets:
            if path in resolved:
                authority = resolved[path]
                if authority is None:
                    unknown.append(path)
                    continue

                groups.setdefault(
                    authority,
                    [],
                ).append(path)
                continue

            if path in unresolved_by_path:
                unknown.append(path)
                continue

            if path not in represented:
                missing.append(path)

        if task.invalid_targets:
            diagnostics.append(
                _diagnostic(
                    "UNRESOLVED_TARGET",
                    _unresolved_severity(stage),
                    (
                        "Task contains path-like values that cannot "
                        "be normalized as repository targets."
                    ),
                    targets=list(
                        task.invalid_targets
                    ),
                    **_task_fields(task),
                )
            )

        if missing:
            diagnostics.append(
                _diagnostic(
                    "STALE_BOUNDARY",
                    _scope_severity(stage),
                    (
                        "Task names write targets that are not "
                        "represented in the current Change Boundary."
                    ),
                    targets=missing,
                    **_task_fields(task),
                )
            )

        authorities = list(groups)

        if len(authorities) > 1:
            diagnostics.append(
                _diagnostic(
                    "MULTI_AUTHORITY_TASK",
                    "warning",
                    (
                        "Task write targets span multiple primary "
                        "SpecDD authorities."
                    ),
                    targets=list(task.targets),
                    authorities=authorities,
                    authorityGroups=[
                        {
                            "authority": authority,
                            "targets": paths,
                        }
                        for authority, paths in groups.items()
                    ],
                    **_task_fields(task),
                )
            )

        unresolved_targets = list(
            dict.fromkeys(
                [
                    *unknown,
                    *missing,
                    *task.invalid_targets,
                ]
            )
        )

        if unresolved_targets:
            classification = "UNRESOLVED"
        elif len(authorities) > 1:
            classification = "CROSS_BOUNDARY"
        elif len(authorities) == 1:
            classification = "NORMAL"
        elif task.spec_targets:
            classification = "SPEC_ONLY"
        else:
            classification = "NO_WRITE_TARGETS"

        task_results.append(
            {
                "order": task.order,
                "id": task.task_id,
                "story": task.story,
                "text": task.text,
                "writeTargets": list(task.targets),
                "specTargets": list(task.spec_targets),
                "authorities": authorities,
                "authorityCount": len(authorities),
                "authorityGroups": [
                    {
                        "authority": authority,
                        "targets": paths,
                    }
                    for authority, paths in groups.items()
                ],
                "unresolvedTargets": unresolved_targets,
                "classification": classification,
            }
        )

    if stage == "implementation":
        unknown_authority = list(
            dict.fromkeys(
                [
                    *unknown_boundary_paths,
                    *unresolved_without_path,
                ]
            )
        )
        if unknown_authority:
            diagnostics.append(
                _diagnostic(
                    "AUTHORITY_VIOLATION",
                    "blocking",
                    (
                        "Implementation cannot proceed while the "
                        "current boundary contains unknown or "
                        "conflicting write authority."
                    ),
                    targets=unknown_authority,
                )
            )

    counts = Counter(
        diagnostic["severity"]
        for diagnostic in diagnostics
    )
    severity_counts = {
        severity: counts.get(
            severity,
            0,
        )
        for severity in SEVERITIES
    }

    return {
        "schemaVersion": 1,
        "feature": feature,
        "stage": stage,
        "tasks": task_results,
        "diagnostics": diagnostics,
        "summary": {
            "taskCount": len(task_results),
            "diagnosticCount": len(diagnostics),
            "countsBySeverity": severity_counts,
            "blocking": severity_counts["blocking"] > 0,
        },
    }
