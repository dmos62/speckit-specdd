from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from boundary_builder import build_change_boundary
from boundary_paths import resolve_root
from boundary_runtime import (
    _locate_executable,
    _run,
    normalize_command_output,
)
from boundary_schema import load_schema
from boundary_schema_validation import validate_boundary
from boundary_types import BoundaryError
from cli_output import (
    FAIL_ON as _FAIL_ON,
    result_exit_code as _result_exit_code,
    root_path as _root_path,
    write_json_output as _write_output,
)
from verification_engine import verify_change_set
from verification_git import (
    authorization_snapshot_path,
    collect_git_changes,
    load_authorization_git_baseline,
    load_authorization_plan,
)
from verification_types import VerificationError

_SPEC_PLAN_FILENAME = "authorization-spec-evolution.json"
_GIT_BASELINE_FILENAME = "authorization-git-baseline.json"


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify actual Git changes against the immutable SpecDD "
            "authorization evidence."
        )
    )
    parser.add_argument(
        "--root",
        help="Repository root; defaults to repository discovery",
    )
    parser.add_argument(
        "--authorization-snapshot",
        help=(
            "Authorization boundary snapshot; defaults to current worktree "
            "Git metadata"
        ),
    )
    parser.add_argument(
        "--spec-evolution-plan",
        help=(
            "Authorization-time specification/control selection plan; "
            "defaults beside the authorization boundary snapshot"
        ),
    )
    parser.add_argument(
        "--git-baseline",
        help=(
            "Authorization-time Git baseline; defaults beside the "
            "authorization boundary snapshot"
        ),
    )
    parser.add_argument(
        "--feature-dir",
        required=True,
        help=(
            "Active Spec Kit feature directory; excluded from "
            "implementation writes"
        ),
    )
    parser.add_argument(
        "--feature",
        help="Expected active feature identifier",
    )
    parser.add_argument(
        "--schema",
        help="Override the Change Boundary schema path",
    )
    parser.add_argument(
        "--specdd",
        default="specdd",
        help="SpecDD CLI executable (default: specdd)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Output path, or '-' for stdout (default)",
    )
    parser.add_argument(
        "--fail-on",
        choices=_FAIL_ON,
        default="never",
        help=(
            "Return status 1 when the selected diagnostic "
            "threshold is present"
        ),
    )
    return parser.parse_args(argv)


def _load_snapshot(
    path: Path,
) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise VerificationError(
            f"Authorization snapshot was not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(
            "Authorization snapshot is invalid JSON: "
            f"{path}: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise VerificationError(
            "Authorization snapshot root must be an object: "
            f"{path}"
        )
    return value


def _empty_actual(
    planned: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "feature": planned["feature"],
        "targets": [],
        "authorities": [],
        "crossBoundary": False,
        "unresolved": [],
        "generation": planned["generation"],
    }


def _specdd_lint(
    root: Path,
    executable: str,
) -> dict[str, Any]:
    command = _locate_executable(
        executable
    )
    result = _run(
        [command, "lint"],
        root,
        subprocess.run,
    )
    return {
        "exitCode": result.returncode,
        "stdout": normalize_command_output(
            root,
            result.stdout,
        ),
        "stderr": normalize_command_output(
            root,
            result.stderr,
        ),
    }


def _evidence_path(
    root: Path,
    snapshot: Path,
    explicit: str | None,
    filename: str,
) -> Path:
    return (
        _root_path(root, explicit)
        if explicit
        else snapshot.with_name(filename)
    )


def _spec_plan_path(
    root: Path,
    snapshot: Path,
    explicit: str | None,
) -> Path:
    return _evidence_path(
        root,
        snapshot,
        explicit,
        _SPEC_PLAN_FILENAME,
    )


def _git_baseline_path(
    root: Path,
    snapshot: Path,
    explicit: str | None,
) -> Path:
    return _evidence_path(
        root,
        snapshot,
        explicit,
        _GIT_BASELINE_FILENAME,
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        schema = load_schema(
            root,
            args.schema,
        )
        snapshot_path = (
            _root_path(
                root,
                args.authorization_snapshot,
            )
            if args.authorization_snapshot
            else authorization_snapshot_path(root)
        )
        planned = _load_snapshot(
            snapshot_path
        )
        validate_boundary(
            planned,
            schema,
        )
        spec_targets, control_targets = load_authorization_plan(
            root,
            _spec_plan_path(
                root,
                snapshot_path,
                args.spec_evolution_plan,
            ),
            planned,
        )
        baseline_path = _git_baseline_path(
            root,
            snapshot_path,
            args.git_baseline,
        )
        baseline = load_authorization_git_baseline(
            root,
            baseline_path,
            planned,
        )
        changes = collect_git_changes(
            root,
            feature_dir=args.feature_dir,
            baseline=baseline,
        )
        existing_targets = [
            item.path
            for item in changes.writes
            if not item.deleted
        ]
        if existing_targets:
            actual = build_change_boundary(
                root,
                existing_targets,
                feature=str(planned["feature"]),
                schema=schema,
                executable=args.specdd,
            )
        else:
            actual = _empty_actual(
                planned
            )
            validate_boundary(
                actual,
                schema,
            )

        result = verify_change_set(
            planned,
            actual,
            changes,
            lint=_specdd_lint(
                root,
                args.specdd,
            ),
            expected_feature=args.feature,
            planned_spec_targets=spec_targets,
            planned_control_targets=control_targets,
        )
        result["authorizationGitBaseline"] = {
            "path": str(baseline_path),
            "head": baseline["head"],
            "excludedPreauthorizationCount": len(
                changes.preauthorization
            ),
            "excludedPreauthorization": [
                {
                    "path": item.path,
                    "status": item.status,
                    "deleted": item.deleted,
                }
                for item in changes.preauthorization
            ],
        }
        _write_output(
            root,
            result,
            args.output,
        )
        return _result_exit_code(
            result,
            args.fail_on,
        )
    except (
        BoundaryError,
        VerificationError,
        OSError,
    ) as exc:
        print(
            f"verification.py: {exc}",
            file=sys.stderr,
        )
        return 2
