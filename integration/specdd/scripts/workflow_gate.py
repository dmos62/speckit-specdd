#!/usr/bin/env python3
"""Run deterministic SpecDD gates inside the Spec Kit workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SCRIPT_DIR),
    )

from boundary_builder import (  # noqa: E402
    build_change_boundary,
    write_boundary,
)
from boundary_paths import (  # noqa: E402
    normalize_target,
    resolve_root,
)
from boundary_schema import load_schema  # noqa: E402
from boundary_schema_validation import validate_boundary  # noqa: E402
from boundary_types import BoundaryError  # noqa: E402
from validation_cli import (  # noqa: E402
    _result_exit_code as validation_exit_code,
    main as validation_main,
)
from validation_engine import validate_feature  # noqa: E402
from validation_tasks import (  # noqa: E402
    extract_repository_targets,
    parse_tasks_file,
)
from validation_types import ValidationError  # noqa: E402
from verification_cli import main as verification_main  # noqa: E402
from verification_git import (  # noqa: E402
    authorization_snapshot_path,
    write_authorization_snapshot,
)
from verification_types import VerificationError  # noqa: E402


class WorkflowGateError(RuntimeError):
    """A structural workflow gate cannot run safely."""


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run structural SpecDD context, task validation, "
            "authorization, or verification."
        )
    )
    parser.add_argument(
        "stage",
        choices=(
            "context",
            "tasks",
            "authorize",
            "verify",
        ),
    )
    parser.add_argument(
        "--root",
        help=(
            "Repository root; defaults to repository discovery"
        ),
    )
    return parser.parse_args(
        argv
    )


def _active_feature(
    root: Path,
) -> tuple[str, Path, str]:
    configured = os.environ.get(
        "SPECIFY_FEATURE_DIRECTORY"
    )
    if not configured:
        state_path = (
            root
            / ".specify"
            / "feature.json"
        )
        try:
            state = json.loads(
                state_path.read_text(
                    encoding="utf-8",
                )
            )
        except FileNotFoundError as exc:
            raise WorkflowGateError(
                "Spec Kit active feature state is missing"
            ) from exc
        except json.JSONDecodeError as exc:
            raise WorkflowGateError(
                "Spec Kit active feature state is invalid JSON"
            ) from exc

        configured = (
            state.get(
                "feature_directory"
            )
            if isinstance(
                state,
                dict,
            )
            else None
        )

    if (
        not isinstance(
            configured,
            str,
        )
        or not configured.strip()
    ):
        raise WorkflowGateError(
            "Spec Kit active feature directory is not configured"
        )

    try:
        target = normalize_target(
            root,
            configured,
        )
    except BoundaryError as exc:
        raise WorkflowGateError(
            f"Active feature directory is invalid: {exc}"
        ) from exc

    if not target.absolute_path.is_dir():
        raise WorkflowGateError(
            "Active feature directory does not exist: "
            + str(
                target.absolute_path
            )
        )

    return (
        target.absolute_path.name,
        target.absolute_path,
        target.path,
    )


def _unique(
    values: Iterable[str],
) -> list[str]:
    return list(
        dict.fromkeys(
            values
        )
    )


def _plan_targets(
    root: Path,
    feature_dir: Path,
    feature_path: str,
) -> list[str]:
    plan_path = (
        feature_dir
        / "plan.md"
    )
    try:
        text = plan_path.read_text(
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise WorkflowGateError(
            f"Spec Kit plan was not found: {plan_path}"
        ) from exc

    targets, _, _ = extract_repository_targets(
        root,
        text,
    )
    prefix = (
        feature_path.rstrip("/")
        + "/"
    )
    return [
        path
        for path in targets
        if (
            path != feature_path
            and not path.startswith(
                prefix
            )
        )
    ]


def _task_targets(
    root: Path,
    task_path: Path,
) -> list[str]:
    try:
        tasks = parse_tasks_file(
            root,
            task_path,
        )
    except FileNotFoundError as exc:
        raise WorkflowGateError(
            f"Spec Kit task file was not found: {task_path}"
        ) from exc

    return _unique(
        path
        for task in tasks
        for path in task.targets
    )


def _refresh_boundary(
    root: Path,
    feature: str,
    output: Path,
    targets: Sequence[str],
    *,
    require_targets: bool,
) -> dict[str, object] | None:
    if not targets:
        output.unlink(
            missing_ok=True
        )
        if require_targets:
            raise WorkflowGateError(
                "Task-stage SpecDD validation requires at least one "
                "exact non-spec implementation target"
            )
        return None

    schema = load_schema(
        root
    )
    value = build_change_boundary(
        root,
        targets,
        feature=feature,
        schema=schema,
    )
    write_boundary(
        value,
        output,
    )
    return value


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
        "boundary": normalize_target(
            root,
            str(output),
        ).path,
        "targets": [
            item.get(
                "path"
            )
            for item in value.get(
                "targets",
                [],
            )
            if isinstance(
                item,
                dict,
            )
        ],
        "authorities": value.get(
            "authorities",
            [],
        ),
        "crossBoundary": value.get(
            "crossBoundary",
            False,
        ),
        "unresolved": value.get(
            "unresolved",
            [],
        ),
    }


def _require_file(
    path: Path,
    label: str,
) -> None:
    if not path.is_file():
        raise WorkflowGateError(
            f"{label} was not found: {path}"
        )


def _load_boundary(
    path: Path,
) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )
    except FileNotFoundError as exc:
        raise WorkflowGateError(
            f"Change Boundary was not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise WorkflowGateError(
            f"Change Boundary is invalid JSON: {path}: {exc}"
        ) from exc

    if not isinstance(
        value,
        dict,
    ):
        raise WorkflowGateError(
            f"Change Boundary root must be an object: {path}"
        )
    return value


def _authorize(
    root: Path,
    feature: str,
    boundary_path: Path,
    task_path: Path,
) -> int:
    schema = load_schema(
        root
    )
    boundary = _load_boundary(
        boundary_path
    )
    validate_boundary(
        boundary,
        schema,
    )
    tasks = parse_tasks_file(
        root,
        task_path,
    )
    result = validate_feature(
        boundary,
        tasks,
        stage="implementation",
        expected_feature=feature,
    )
    status = validation_exit_code(
        result,
        "error",
    )
    if status != 0:
        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )
        return status

    snapshot = write_authorization_snapshot(
        root,
        boundary,
    )
    result["authorizationSnapshot"] = {
        "path": str(
            snapshot
        ),
        "stored": True,
    }
    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def run_stage(
    root: Path,
    stage: str,
) -> int:
    (
        feature,
        feature_dir,
        feature_path,
    ) = _active_feature(
        root
    )
    boundary_path = (
        feature_dir
        / ".specdd"
        / "boundary.json"
    )
    task_path = (
        feature_dir
        / "tasks.md"
    )

    if stage == "context":
        value = _refresh_boundary(
            root,
            feature,
            boundary_path,
            _plan_targets(
                root,
                feature_dir,
                feature_path,
            ),
            require_targets=False,
        )
        print(
            json.dumps(
                _boundary_summary(
                    root,
                    feature,
                    boundary_path,
                    value,
                ),
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
            _task_targets(
                root,
                task_path,
            ),
            require_targets=True,
        )
        print(
            json.dumps(
                _boundary_summary(
                    root,
                    feature,
                    boundary_path,
                    value,
                ),
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

    _require_file(
        boundary_path,
        "Change Boundary",
    )

    if stage == "authorize":
        _require_file(
            task_path,
            "Spec Kit task file",
        )
        return _authorize(
            root,
            feature,
            boundary_path,
            task_path,
        )

    snapshot_path = authorization_snapshot_path(
        root
    )
    _require_file(
        snapshot_path,
        "Authorization snapshot",
    )
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


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(
        argv
    )
    try:
        root = resolve_root(
            args.root
        )
        return run_stage(
            root,
            args.stage,
        )
    except (
        BoundaryError,
        ValidationError,
        VerificationError,
        WorkflowGateError,
        OSError,
    ) as exc:
        print(
            f"workflow_gate.py: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
