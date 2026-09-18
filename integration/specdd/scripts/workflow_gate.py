#!/usr/bin/env python3
"""Run deterministic SpecDD gates inside the Spec Kit workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from boundary_paths import resolve_root  # noqa: E402
from boundary_schema import load_schema  # noqa: E402
from boundary_schema_validation import validate_boundary  # noqa: E402
from boundary_types import BoundaryError  # noqa: E402
from validation_cli import (  # noqa: E402
    _result_exit_code as validation_exit_code,
    main as validation_main,
)
from validation_engine import validate_feature  # noqa: E402
from validation_permissions import (  # noqa: E402
    project_task_modification_permissions,
    requires_permission_projection,
)
from validation_tasks import parse_tasks_file  # noqa: E402
from validation_types import TaskRecord, ValidationError  # noqa: E402
from verification_cli import main as verification_main  # noqa: E402
from verification_git import (  # noqa: E402
    authorization_snapshot_path,
    authorization_spec_plan_path,
    write_authorization_evidence,
)
from verification_types import VerificationError  # noqa: E402
from workflow_gate_state import (  # noqa: E402,F401
    WorkflowGateError,
    _active_feature,
    _boundary_summary,
    _load_boundary,
    _plan_targets,
    _refresh_boundary,
    _require_file,
    _task_targets,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run structural SpecDD context, task validation, "
            "authorization, or verification."
        )
    )
    parser.add_argument(
        "stage",
        choices=("context", "tasks", "authorize", "verify"),
    )
    parser.add_argument(
        "--root",
        help="Repository root; defaults to repository discovery",
    )
    return parser.parse_args(argv)


def _planned_spec_evolution_targets(tasks: Sequence[TaskRecord]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            target
            for task in tasks
            if len(task.evolution_markers) == 1
            for target in task.spec_targets
        )
    )


def _authorize(
    root: Path,
    feature: str,
    boundary_path: Path,
    task_path: Path,
) -> int:
    schema = load_schema(root)
    boundary = _load_boundary(boundary_path)
    validate_boundary(boundary, schema)
    tasks = parse_tasks_file(root, task_path)
    permissions = {}
    if requires_permission_projection(boundary, tasks):
        permissions = project_task_modification_permissions(root, boundary, tasks)
    result = validate_feature(
        boundary,
        tasks,
        stage="implementation",
        expected_feature=feature,
        task_permissions=permissions,
    )
    status = validation_exit_code(result, "error")
    if status != 0:
        print(json.dumps(result, indent=2, sort_keys=True))
        return status

    spec_targets = _planned_spec_evolution_targets(tasks)
    snapshot, spec_plan = write_authorization_evidence(
        root,
        boundary,
        spec_targets,
    )
    result["authorizationSnapshot"] = {
        "path": str(snapshot),
        "stored": True,
        "plannedSpecEvolution": {
            "path": str(spec_plan),
            "targets": list(spec_targets),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_stage(root: Path, stage: str) -> int:
    feature, feature_dir, feature_path = _active_feature(root)
    boundary_path = feature_dir / ".specdd" / "boundary.json"
    task_path = feature_dir / "tasks.md"

    if stage == "context":
        value = _refresh_boundary(
            root,
            feature,
            boundary_path,
            _plan_targets(root, feature_dir, feature_path),
            require_targets=False,
        )
        print(
            json.dumps(
                _boundary_summary(root, feature, boundary_path, value),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if stage == "tasks":
        value = _refresh_boundary(
            root,
            feature,
            boundary_path,
            _task_targets(root, task_path),
            require_targets=True,
        )
        print(
            json.dumps(
                _boundary_summary(root, feature, boundary_path, value),
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return validation_main(
            [
                "--root",
                str(root),
                "--feature",
                feature,
                "--boundary",
                str(boundary_path),
                "--tasks",
                str(task_path),
                "--stage",
                "tasks",
                "--fail-on",
                "error",
            ]
        )

    _require_file(boundary_path, "Change Boundary")
    if stage == "authorize":
        _require_file(task_path, "Spec Kit task file")
        return _authorize(root, feature, boundary_path, task_path)

    snapshot_path = authorization_snapshot_path(root)
    spec_plan_path = authorization_spec_plan_path(root)
    _require_file(snapshot_path, "Authorization snapshot")
    _require_file(spec_plan_path, "Authorization specification plan")
    return verification_main(
        [
            "--root",
            str(root),
            "--feature",
            feature,
            "--feature-dir",
            str(feature_dir),
            "--authorization-snapshot",
            str(snapshot_path),
            "--fail-on",
            "error",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        return run_stage(root, args.stage)
    except (
        BoundaryError,
        ValidationError,
        VerificationError,
        WorkflowGateError,
        OSError,
    ) as exc:
        print(f"workflow_gate.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
