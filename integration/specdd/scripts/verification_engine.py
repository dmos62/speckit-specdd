from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from verification_types import (
    IMMUTABLE_BOOTSTRAP_CONTROL,
    PROJECT_BOOTSTRAP_CONTROL,
    ChangeSet,
    VerificationError,
)

_SEVERITIES = ("info", "warning", "error", "blocking")


def _diagnostic(
    code: str,
    severity: str,
    dimension: str,
    message: str,
    **fields: Any,
) -> dict[str, Any]:
    value = {
        "code": code,
        "severity": severity,
        "dimension": dimension,
        "message": message,
    }
    value.update(
        {
            key: field
            for key, field in fields.items()
            if field not in (None, [], ())
        }
    )
    return value


def _target_map(boundary: Mapping[str, Any]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for item in boundary.get("targets", []):
        if not isinstance(item, Mapping):
            continue
        path = item.get("path")
        authority = item.get("primaryAuthority")
        if isinstance(path, str):
            result[path] = authority if isinstance(authority, str) else None
    return result


def _unresolved_map(
    boundary: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in boundary.get("unresolved", []):
        if (
            isinstance(item, Mapping)
            and isinstance(item.get("normalizedPath"), str)
        ):
            result[item["normalizedPath"]] = item
    return result


def _change_record(item: Any) -> dict[str, Any]:
    return {
        "path": item.path,
        "status": item.status,
        "deleted": item.deleted,
    }


def _spec_diagnostics(
    changes: ChangeSet,
    planned_spec_targets: Sequence[str],
) -> list[dict[str, Any]]:
    planned = set(planned_spec_targets)
    selected = [item for item in changes.specs if item.path in planned]
    unplanned = [item for item in changes.specs if item.path not in planned]
    diagnostics: list[dict[str, Any]] = []
    if selected:
        diagnostics.append(
            _diagnostic(
                "SPEC_EVOLUTION_PRESENT",
                "info",
                "system",
                "Changed SpecDD specifications were selected by explicit "
                "evolution tasks. They do not grant authority to the current "
                "implementation operation.",
                targets=[item.path for item in selected],
                changes=[_change_record(item) for item in selected],
            )
        )
    if unplanned:
        diagnostics.append(
            _diagnostic(
                "UNPLANNED_SPEC_EVOLUTION",
                "blocking",
                "governance",
                "SpecDD specifications changed without being selected by an "
                "explicit evolution task in the authorization evidence.",
                targets=[item.path for item in unplanned],
                changes=[_change_record(item) for item in unplanned],
            )
        )
    return diagnostics


def _control_diagnostics(
    changes: ChangeSet,
    planned: Mapping[str, str],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for item in changes.controls:
        if item.path == IMMUTABLE_BOOTSTRAP_CONTROL:
            diagnostics.append(
                _diagnostic(
                    "CONTROL_STATE_VIOLATION",
                    "blocking",
                    "governance",
                    "The immutable SpecDD bootstrap control file changed.",
                    targets=[item.path],
                    changes=[_change_record(item)],
                )
            )
            continue

        source = planned.get(item.path)
        if item.path == PROJECT_BOOTSTRAP_CONTROL and source is not None:
            diagnostics.append(
                _diagnostic(
                    "CONTROL_STATE_CHANGED",
                    "info",
                    "governance",
                    "The project SpecDD bootstrap override changed after being "
                    "explicitly selected for this operation.",
                    targets=[item.path],
                    selectedBy=source,
                    changes=[_change_record(item)],
                )
            )
            continue

        diagnostics.append(
            _diagnostic(
                "CONTROL_STATE_VIOLATION",
                "blocking",
                "governance",
                "Root SpecDD control state changed without an applicable "
                "explicit authorization selection.",
                targets=[item.path],
                changes=[_change_record(item)],
            )
        )
    return diagnostics


def verify_change_set(
    planned: Mapping[str, Any],
    actual: Mapping[str, Any],
    changes: ChangeSet,
    *,
    lint: Mapping[str, Any],
    expected_feature: str | None = None,
    planned_spec_targets: Sequence[str] = (),
    planned_control_targets: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    feature = planned.get("feature")
    if not isinstance(feature, str) or not feature:
        raise VerificationError(
            "Planned Change Boundary has no feature identifier"
        )

    diagnostics: list[dict[str, Any]] = []
    planned_targets = _target_map(planned)
    actual_targets = _target_map(actual)
    actual_unresolved = _unresolved_map(actual)
    planned_authorities = {
        item
        for item in planned.get("authorities", [])
        if isinstance(item, str)
    }
    control_targets = planned_control_targets or {}

    if expected_feature is not None and feature != expected_feature:
        diagnostics.append(
            _diagnostic(
                "STALE_BOUNDARY",
                "blocking",
                "system",
                "The planned Change Boundary does not belong to the active feature.",
                expectedFeature=expected_feature,
                boundaryFeature=feature,
            )
        )

    for change in changes.writes:
        path = change.path
        planned_authority = planned_targets.get(path)
        if change.deleted:
            if (
                planned_authority is None
                or planned_authority not in planned_authorities
            ):
                diagnostics.append(
                    _diagnostic(
                        "AUTHORITY_VIOLATION",
                        "blocking",
                        "authority",
                        "A deleted implementation target cannot be freshly "
                        "resolved and was not authorized by the Change Boundary.",
                        targets=[path],
                    )
                )
            continue

        actual_authority = actual_targets.get(path)
        if actual_authority is None:
            unresolved = actual_unresolved.get(path)
            diagnostics.append(
                _diagnostic(
                    "AUTHORITY_VIOLATION",
                    "blocking",
                    "authority",
                    "Actual implementation write authority is unknown or "
                    "conflicting after fresh SpecDD resolution.",
                    targets=[path],
                    boundaryCode=(
                        unresolved.get("code")
                        if unresolved
                        else None
                    ),
                    candidateAuthorities=(
                        unresolved.get("candidateAuthorities")
                        if unresolved
                        else None
                    ),
                )
            )
            continue

        if actual_authority not in planned_authorities:
            diagnostics.append(
                _diagnostic(
                    "AUTHORITY_VIOLATION",
                    "blocking",
                    "authority",
                    "Actual implementation writes introduce a SpecDD authority "
                    "domain absent from the planned Change Boundary.",
                    targets=[path],
                    actualAuthority=actual_authority,
                    plannedAuthorities=sorted(planned_authorities),
                )
            )
            continue

        if (
            planned_authority is not None
            and planned_authority != actual_authority
        ):
            diagnostics.append(
                _diagnostic(
                    "AUTHORITY_VIOLATION",
                    "blocking",
                    "authority",
                    "Fresh SpecDD resolution assigns a different authority than "
                    "the operation's planned authority snapshot.",
                    targets=[path],
                    plannedAuthority=planned_authority,
                    actualAuthority=actual_authority,
                )
            )
            continue

        if planned_authority is None:
            diagnostics.append(
                _diagnostic(
                    "SPECDD_DRIFT",
                    "error",
                    "system",
                    "Actual implementation writes include an unplanned target "
                    "inside an already planned authority domain.",
                    targets=[path],
                    actualAuthority=actual_authority,
                )
            )

    diagnostics.extend(
        _spec_diagnostics(changes, planned_spec_targets)
    )
    diagnostics.extend(
        _control_diagnostics(changes, control_targets)
    )

    exit_code = lint.get("exitCode")
    if not isinstance(exit_code, int):
        raise VerificationError(
            "SpecDD lint result does not contain an integer exitCode"
        )
    if exit_code != 0:
        diagnostics.append(
            _diagnostic(
                "SPECDD_VIOLATION",
                "blocking",
                "system",
                "SpecDD lint failed for the resulting repository state.",
                exitCode=exit_code,
            )
        )

    counts = Counter(item["severity"] for item in diagnostics)
    severity_counts = {
        name: counts.get(name, 0)
        for name in _SEVERITIES
    }
    return {
        "schemaVersion": 1,
        "feature": feature,
        "changes": {
            "writeTargets": [
                _change_record(item)
                for item in changes.writes
            ],
            "specTargets": [
                _change_record(item)
                for item in changes.specs
            ],
            "controlTargets": [
                _change_record(item)
                for item in changes.controls
            ],
            "featureArtifacts": [
                _change_record(item)
                for item in changes.feature_artifacts
            ],
            "excludedGenerated": [
                _change_record(item)
                for item in changes.generated
            ],
        },
        "planned": {
            "targetCount": len(planned_targets),
            "authorities": sorted(planned_authorities),
            "specEvolutionTargets": list(planned_spec_targets),
            "controlTargets": [
                {
                    "path": path,
                    "selectedBy": source,
                }
                for path, source in sorted(control_targets.items())
            ],
        },
        "actual": {
            "targets": actual.get("targets", []),
            "authorities": actual.get("authorities", []),
            "crossBoundary": actual.get("crossBoundary", False),
            "unresolved": actual.get("unresolved", []),
        },
        "specddLint": dict(lint),
        "diagnostics": diagnostics,
        "summary": {
            "diagnosticCount": len(diagnostics),
            "countsBySeverity": severity_counts,
            "blocking": severity_counts["blocking"] > 0,
        },
    }
