from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from verification_types import (
    ChangeSet,
    VerificationError,
)

_SEVERITIES = (
    "info",
    "warning",
    "error",
    "blocking",
)


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
            key: item
            for key, item in fields.items()
            if item not in (None, [], ())
        }
    )
    return value


def _target_map(
    boundary: Mapping[str, Any],
) -> dict[str, str | None]:
    result: dict[str, str | None] = {}

    for item in boundary.get("targets", []):
        if not isinstance(item, Mapping):
            continue

        path = item.get("path")
        authority = item.get("primaryAuthority")
        if isinstance(path, str):
            result[path] = (
                authority
                if isinstance(authority, str)
                else None
            )

    return result


def _unresolved_map(
    boundary: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}

    for item in boundary.get("unresolved", []):
        if not isinstance(item, Mapping):
            continue

        path = item.get("normalizedPath")
        if isinstance(path, str):
            result[path] = item

    return result


def _change_record(
    item: Any,
) -> dict[str, Any]:
    return {
        "path": item.path,
        "status": item.status,
        "deleted": item.deleted,
    }


def verify_change_set(
    planned: Mapping[str, Any],
    actual: Mapping[str, Any],
    changes: ChangeSet,
    *,
    lint: Mapping[str, Any],
    expected_feature: str | None = None,
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

    if (
        expected_feature is not None
        and feature != expected_feature
    ):
        diagnostics.append(
            _diagnostic(
                "STALE_BOUNDARY",
                "blocking",
                "system",
                (
                    "The planned Change Boundary does not belong "
                    "to the active feature."
                ),
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
                        (
                            "A deleted implementation target cannot "
                            "be verified against the current resolver "
                            "and was not authorized by the planned "
                            "Change Boundary."
                        ),
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
                    (
                        "Actual implementation write authority is "
                        "unknown or conflicting after fresh SpecDD "
                        "resolution."
                    ),
                    targets=[path],
                    boundaryCode=(
                        unresolved.get("code")
                        if unresolved is not None
                        else None
                    ),
                    candidateAuthorities=(
                        unresolved.get("candidateAuthorities")
                        if unresolved is not None
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
                    (
                        "Actual implementation writes introduce a "
                        "SpecDD authority domain absent from the "
                        "planned Change Boundary."
                    ),
                    targets=[path],
                    actualAuthority=actual_authority,
                    plannedAuthorities=sorted(
                        planned_authorities
                    ),
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
                    (
                        "Fresh SpecDD resolution assigns a different "
                        "authority than the operation's planned "
                        "authority snapshot."
                    ),
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
                    (
                        "Actual implementation writes include an "
                        "unplanned target inside an already planned "
                        "authority domain."
                    ),
                    targets=[path],
                    actualAuthority=actual_authority,
                )
            )

    if changes.specs:
        diagnostics.append(
            _diagnostic(
                "SPEC_EVOLUTION_PRESENT",
                "info",
                "system",
                (
                    "Changed SpecDD specifications are present. "
                    "They do not grant authority to the current "
                    "implementation operation."
                ),
                targets=[
                    item.path
                    for item in changes.specs
                ],
            )
        )

    if changes.controls:
        diagnostics.append(
            _diagnostic(
                "CONTROL_STATE_CHANGED",
                "warning",
                "governance",
                (
                    "SpecDD bootstrap control files changed and are "
                    "reported separately from implementation writes."
                ),
                targets=[
                    item.path
                    for item in changes.controls
                ],
            )
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

    counts = Counter(
        item["severity"]
        for item in diagnostics
    )
    count_values = {
        severity: counts.get(
            severity,
            0,
        )
        for severity in _SEVERITIES
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
            "authorities": sorted(
                planned_authorities
            ),
        },
        "actual": {
            "targets": actual.get("targets", []),
            "authorities": actual.get("authorities", []),
            "crossBoundary": actual.get(
                "crossBoundary",
                False,
            ),
            "unresolved": actual.get("unresolved", []),
        },
        "specddLint": dict(lint),
        "diagnostics": diagnostics,
        "summary": {
            "diagnosticCount": len(diagnostics),
            "countsBySeverity": count_values,
            "blocking": count_values["blocking"] > 0,
        },
    }
