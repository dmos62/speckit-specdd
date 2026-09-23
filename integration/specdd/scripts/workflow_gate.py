#!/usr/bin/env python3
"""Run deterministic SpecDD gates inside the Spec Kit workflow."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from boundary_paths import normalize_target, resolve_root  # noqa: E402
from boundary_schema import load_schema  # noqa: E402
from boundary_schema_validation import validate_boundary  # noqa: E402
from boundary_types import BoundaryError  # noqa: E402
from validation_cli import _result_exit_code as validation_exit_code, main as validation_main  # noqa: E402
from validation_engine import SEVERITIES, validate_feature  # noqa: E402
from validation_tasks import parse_tasks_file  # noqa: E402
from validation_types import TaskRecord, ValidationError, diagnostic  # noqa: E402
from verification_cli import main as verification_main  # noqa: E402
from verification_git import (  # noqa: E402
    authorization_git_baseline_path,
    authorization_snapshot_path,
    authorization_spec_plan_path,
    write_authorization_evidence,
)
from verification_types import (  # noqa: E402
    EDITABLE_BOOTSTRAP_CONTROLS,
    IMMUTABLE_BOOTSTRAP_CONTROL,
    VerificationError,
)
from workflow_gate_state import (  # noqa: E402,F401
    WorkflowGateError,
    _active_feature,
    _boundary_summary,
    _load_boundary,
    _plan_targets,
    _refresh_boundary,
    _require_file,
    _specdd_context_diagnostics,
    _task_targets,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run structural SpecDD context, task validation, authorization, or verification."
    )
    parser.add_argument("stage", choices=("context", "tasks", "authorize", "verify"))
    parser.add_argument("--root", help="Repository root; defaults to repository discovery")
    parser.add_argument(
        "--operator-control",
        action="append",
        default=[],
        help=(
            "Explicit operator-selected editable root SpecDD bootstrap override. "
            "May be supplied more than once during authorization."
        ),
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


def _control_selections(
    root: Path, tasks: Sequence[TaskRecord], operator_controls: Sequence[str]
) -> dict[str, str]:
    selections = {path: "workflow" for task in tasks for path in task.control_targets}
    for raw in operator_controls:
        selections[normalize_target(root, raw).path] = "operator"
    return selections


def _control_diagnostics(selections: dict[str, str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path, source in sorted(selections.items()):
        if path == IMMUTABLE_BOOTSTRAP_CONTROL:
            findings.append(
                diagnostic(
                    "CONTROL_STATE_VIOLATION",
                    "blocking",
                    "The immutable SpecDD bootstrap control file cannot be selected for modification.",
                    targets=[path],
                    selectedBy=source,
                )
            )
        elif path not in EDITABLE_BOOTSTRAP_CONTROLS:
            findings.append(
                diagnostic(
                    "CONTROL_STATE_VIOLATION",
                    "blocking",
                    "Root SpecDD control state is not an editable bootstrap override.",
                    targets=[path],
                    selectedBy=source,
                )
            )
    return findings


def _extend_diagnostics(
    result: dict[str, object], findings: Sequence[dict[str, object]]
) -> None:
    if not findings:
        return
    diagnostics = result["diagnostics"]
    summary = result["summary"]
    if not isinstance(diagnostics, list) or not isinstance(summary, dict):
        raise WorkflowGateError("Validation output has an invalid shape")
    diagnostics.extend(findings)
    counts = Counter(item.get("severity") for item in diagnostics if isinstance(item, dict))
    severity_counts = {severity: counts.get(severity, 0) for severity in SEVERITIES}
    summary["diagnosticCount"] = len(diagnostics)
    summary["countsBySeverity"] = severity_counts
    summary["blocking"] = severity_counts["blocking"] > 0


def _authorize(
    root: Path,
    feature: str,
    boundary_path: Path,
    task_path: Path,
    operator_controls: Sequence[str] = (),
) -> int:
    schema = load_schema(root)
    boundary = _load_boundary(boundary_path)
    validate_boundary(boundary, schema)
    context_findings = _specdd_context_diagnostics(root, boundary, schema)
    tasks = parse_tasks_file(root, task_path)
    result = validate_feature(
        boundary,
        tasks,
        stage="implementation",
        expected_feature=feature,
    )
    result["specddContextFresh"] = not context_findings
    _extend_diagnostics(result, context_findings)
    selections = _control_selections(root, tasks, operator_controls)
    result["controlSelections"] = [
        {"path": path, "selectedBy": source}
        for path, source in sorted(selections.items())
    ]
    _extend_diagnostics(result, _control_diagnostics(selections))
    status = validation_exit_code(result, "error")
    if status != 0:
        print(json.dumps(result, indent=2, sort_keys=True))
        return status

    spec_targets = _planned_spec_evolution_targets(tasks)
    snapshot, spec_plan = write_authorization_evidence(
        root, boundary, spec_targets, control_selections=selections
    )
    git_baseline = spec_plan.with_name("authorization-git-baseline.json")
    result["authorizationSnapshot"] = {
        "path": str(snapshot),
        "stored": True,
        "gitBaseline": str(git_baseline),
        "plannedSpecEvolution": {
            "path": str(spec_plan),
            "targets": list(spec_targets),
            "controlTargets": result["controlSelections"],
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_stage(
    root: Path, stage: str, *, operator_controls: Sequence[str] = ()
) -> int:
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
        print(json.dumps(_boundary_summary(root, feature, boundary_path, value), indent=2, sort_keys=True))
        return 0

    if stage == "tasks":
        value = _refresh_boundary(
            root,
            feature,
            boundary_path,
            _task_targets(root, task_path),
            require_targets=True,
        )
        print(json.dumps(_boundary_summary(root, feature, boundary_path, value), sort_keys=True), file=sys.stderr)
        return validation_main([
            "--root", str(root), "--feature", feature, "--boundary", str(boundary_path),
            "--tasks", str(task_path), "--stage", "tasks", "--fail-on", "error",
        ])

    _require_file(boundary_path, "Change Boundary")
    if stage == "authorize":
        _require_file(task_path, "Spec Kit task file")
        return _authorize(root, feature, boundary_path, task_path, operator_controls)

    snapshot_path = authorization_snapshot_path(root)
    spec_plan_path = authorization_spec_plan_path(root)
    git_baseline_path = authorization_git_baseline_path(root)
    _require_file(snapshot_path, "Authorization snapshot")
    _require_file(spec_plan_path, "Authorization specification plan")
    _require_file(git_baseline_path, "Authorization Git baseline")
    return verification_main([
        "--root", str(root), "--feature", feature, "--feature-dir", str(feature_dir),
        "--authorization-snapshot", str(snapshot_path), "--fail-on", "error",
    ])


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        return run_stage(root, args.stage, operator_controls=args.operator_control)
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
