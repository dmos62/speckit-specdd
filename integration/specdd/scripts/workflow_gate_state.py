from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from boundary_builder import (
    build_change_boundary,
    load_boundary_context_evidence,
    write_boundary,
    write_boundary_context_evidence,
)
from boundary_paths import normalize_target
from boundary_schema import load_schema
from boundary_types import BoundaryError
from validation_tasks import (
    extract_repository_targets,
    is_specdd_control_path,
    parse_tasks_file,
)
from validation_types import diagnostic


class WorkflowGateError(RuntimeError):
    """A structural workflow gate cannot run safely."""


def _active_feature(root: Path) -> tuple[str, Path, str]:
    configured = os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if not configured:
        state_path = root / ".specify" / "feature.json"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise WorkflowGateError("Spec Kit active feature state is missing") from exc
        except json.JSONDecodeError as exc:
            raise WorkflowGateError(
                "Spec Kit active feature state is invalid JSON"
            ) from exc
        configured = (
            state.get("feature_directory")
            if isinstance(state, dict)
            else None
        )

    if not isinstance(configured, str) or not configured.strip():
        raise WorkflowGateError(
            "Spec Kit active feature directory is not configured"
        )
    try:
        target = normalize_target(root, configured)
    except BoundaryError as exc:
        raise WorkflowGateError(
            f"Active feature directory is invalid: {exc}"
        ) from exc
    if not target.absolute_path.is_dir():
        raise WorkflowGateError(
            "Active feature directory does not exist: " + str(target.absolute_path)
        )
    return target.absolute_path.name, target.absolute_path, target.path


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _plan_targets(
    root: Path,
    feature_dir: Path,
    feature_path: str,
) -> list[str]:
    plan_path = feature_dir / "plan.md"
    try:
        text = plan_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise WorkflowGateError(f"Spec Kit plan was not found: {plan_path}") from exc

    targets, _, _ = extract_repository_targets(root, text)
    prefix = feature_path.rstrip("/") + "/"
    return [
        path
        for path in targets
        if path != feature_path
        and not path.startswith(prefix)
        and not is_specdd_control_path(path)
    ]


def _task_targets(root: Path, task_path: Path) -> list[str]:
    try:
        tasks = parse_tasks_file(root, task_path)
    except FileNotFoundError as exc:
        raise WorkflowGateError(
            f"Spec Kit task file was not found: {task_path}"
        ) from exc
    return _unique(path for task in tasks for path in task.targets)


def _refresh_boundary(
    root: Path,
    feature: str,
    output: Path,
    targets: Sequence[str],
    *,
    require_targets: bool,
) -> dict[str, object] | None:
    if not targets and not require_targets:
        output.unlink(missing_ok=True)
        return None

    schema = load_schema(root)
    fingerprints: dict[str, str] = {}
    value = build_change_boundary(
        root,
        targets,
        feature=feature,
        schema=schema,
        context_fingerprints=fingerprints,
        allow_empty=not targets,
    )
    write_boundary_context_evidence(
        root,
        value,
        fingerprints,
    )
    write_boundary(value, output)
    return value


def _boundary_target_map(
    boundary: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for item in boundary.get("targets", []):
        if not isinstance(item, Mapping):
            continue
        path = item.get("path")
        if isinstance(path, str):
            result[path] = item
    return result


def _specdd_context_diagnostics(
    root: Path,
    boundary: Mapping[str, object],
    schema: Mapping[str, object],
) -> list[dict[str, object]]:
    try:
        expected_fingerprints = load_boundary_context_evidence(
            root,
            boundary,
        )
    except BoundaryError as exc:
        return [
            diagnostic(
                "STALE_BOUNDARY",
                "blocking",
                "Change Boundary effective SpecDD context evidence is "
                "missing, invalid, or no longer matches the boundary.",
                contextError=str(exc),
            )
        ]

    planned = _boundary_target_map(boundary)
    if not planned:
        return []

    fresh_fingerprints: dict[str, str] = {}
    fresh = build_change_boundary(
        root,
        planned,
        feature=str(boundary["feature"]),
        schema=schema,
        context_fingerprints=fresh_fingerprints,
    )
    current = _boundary_target_map(fresh)
    unresolved = {
        item.get("normalizedPath"): item
        for item in fresh.get("unresolved", [])
        if isinstance(item, Mapping)
        and isinstance(item.get("normalizedPath"), str)
    }

    changes: list[dict[str, object]] = []
    for path, expected_target in planned.items():
        current_target = current.get(path)
        expected_hash = expected_fingerprints.get(path)
        current_hash = fresh_fingerprints.get(path)
        if current_target is None:
            unresolved_item = unresolved.get(path, {})
            changes.append(
                {
                    "path": path,
                    "expectedContextSha256": expected_hash,
                    "boundaryCode": unresolved_item.get("code"),
                }
            )
            continue

        expected_authority = expected_target.get("primaryAuthority")
        current_authority = current_target.get("primaryAuthority")
        if (
            expected_hash != current_hash
            or expected_authority != current_authority
        ):
            changes.append(
                {
                    "path": path,
                    "expectedContextSha256": expected_hash,
                    "actualContextSha256": current_hash,
                    "expectedAuthority": expected_authority,
                    "actualAuthority": current_authority,
                    "expectedResolvedSpecs": expected_target.get("resolvedSpecs"),
                    "actualResolvedSpecs": current_target.get("resolvedSpecs"),
                }
            )

    generation_changed = boundary.get("generation") != fresh.get("generation")
    if not changes and not generation_changed:
        return []

    return [
        diagnostic(
            "STALE_BOUNDARY",
            "blocking",
            "Governing SpecDD context changed after the Change Boundary "
            "was generated. Refresh context before authorization.",
            targets=[item["path"] for item in changes],
            contextChanges=changes,
            generationChanged=True if generation_changed else None,
        )
    ]


def _boundary_summary(
    root: Path,
    feature: str,
    output: Path,
    value: dict[str, object] | None,
) -> dict[str, object]:
    if value is None:
        return {
            "feature": feature,
            "boundary": None,
            "targets": [],
            "authorities": [],
            "crossBoundary": False,
        }
    return {
        "feature": feature,
        "boundary": normalize_target(root, str(output)).path,
        "targets": [
            item.get("path")
            for item in value.get("targets", [])
            if isinstance(item, dict)
        ],
        "authorities": value.get("authorities", []),
        "crossBoundary": value.get("crossBoundary", False),
        "unresolved": value.get("unresolved", []),
    }


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise WorkflowGateError(f"{label} was not found: {path}")


def _load_boundary(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowGateError(f"Change Boundary was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowGateError(
            f"Change Boundary is invalid JSON: {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise WorkflowGateError(f"Change Boundary root must be an object: {path}")
    return value
