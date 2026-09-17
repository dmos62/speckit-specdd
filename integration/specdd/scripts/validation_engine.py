from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from validation_tasks import project_evolution
from validation_types import (
    TaskRecord,
    ValidationError,
    diagnostic,
    project_boundary_authority,
    task_fields,
)
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

def _scope_severity(stage: str) -> str:
    return {
        "planning": "warning",
        "tasks": "error",
        "implementation": "blocking",
    }[stage]

def _unresolved_severity(stage: str) -> str:
    return {
        "planning": "warning",
        "tasks": "error",
        "implementation": "error",
    }[stage]

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
    if expected_feature is not None and feature != expected_feature:
        diagnostics.append(
            diagnostic(
                "STALE_BOUNDARY",
                _scope_severity(stage),
                "Change Boundary feature does not match the active feature.",
                expectedFeature=expected_feature,
                boundaryFeature=feature,
            )
        )

    (
        resolved,
        unresolved_by_path,
        unknown_boundary_paths,
        unresolved_without_path,
        boundary_diagnostics,
    ) = project_boundary_authority(
        boundary,
        unresolved_severity=_unresolved_severity(stage),
    )
    diagnostics.extend(boundary_diagnostics)
    represented = set(resolved) | set(unresolved_by_path)
    task_results: list[dict[str, Any]] = []
    implementation_unknown: list[str] = []
    for task in tasks:
        groups: dict[str, list[str]] = {}
        unknown: list[str] = []
        missing: list[str] = []
        for path in task.targets:
            if path in resolved:
                authority = resolved[path]
                if authority is None:
                    unknown.append(path)
                else:
                    groups.setdefault(
                        authority,
                        [],
                    ).append(path)
            elif path in unresolved_by_path:
                unknown.append(path)
            elif path not in represented:
                missing.append(path)

        if task.invalid_targets:
            diagnostics.append(
                diagnostic(
                    "UNRESOLVED_TARGET",
                    _unresolved_severity(stage),
                    "Task contains invalid repository target paths.",
                    targets=list(task.invalid_targets),
                    **task_fields(task),
                )
            )
        if missing:
            diagnostics.append(
                diagnostic(
                    "STALE_BOUNDARY",
                    _scope_severity(stage),
                    "Task write targets are absent from the current boundary.",
                    targets=missing,
                    **task_fields(task),
                )
            )

        authorities = list(groups)
        authority_groups = [
            {
                "authority": authority,
                "targets": paths,
            }
            for authority, paths in groups.items()
        ]
        if len(authorities) > 1:
            diagnostics.append(
                diagnostic(
                    "MULTI_AUTHORITY_TASK",
                    "warning",
                    "Task write targets span multiple SpecDD authorities.",
                    targets=list(task.targets),
                    authorities=authorities,
                    authorityGroups=authority_groups,
                    **task_fields(task),
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
        implementation_unknown.extend(unresolved_targets)
        evolution, evolution_diagnostics = project_evolution(
            task,
            severity=_scope_severity(stage),
        )
        diagnostics.extend(evolution_diagnostics)

        if task.evolution_markers:
            classification = (
                evolution["classification"]
                if evolution and evolution["classification"]
                else "UNRESOLVED"
            )
        elif unresolved_targets:
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
                "authorityGroups": authority_groups,
                "unresolvedTargets": unresolved_targets,
                "classification": classification,
                "evolution": evolution,
            }
        )

    if stage == "implementation":
        unknown_authority = list(
            dict.fromkeys(
                [
                    *unknown_boundary_paths,
                    *unresolved_without_path,
                    *implementation_unknown,
                ]
            )
        )
        if unknown_authority:
            diagnostics.append(
                diagnostic(
                    "AUTHORITY_VIOLATION",
                    "blocking",
                    "Implementation cannot proceed with unknown authority.",
                    targets=unknown_authority,
                )
            )

    counts = Counter(
        item["severity"]
        for item in diagnostics
    )
    severity_counts = {
        severity: counts.get(
            severity,
            0,
        )
        for severity in SEVERITIES
    }
    evolutions = [
        item["evolution"]
        for item in task_results
        if item["evolution"]
        and item["evolution"]["classification"]
    ]
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
            "evolutionCount": len(evolutions),
            "freshBoundaryRequiredAfterEvolution": bool(evolutions),
            "authorityContextEndsAfterEvolution": any(
                item["endsAuthorityContext"]
                for item in evolutions
            ),
        },
    }
