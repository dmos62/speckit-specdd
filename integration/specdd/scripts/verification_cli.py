from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from boundary_builder import build_change_boundary
from boundary_paths import resolve_root
from boundary_runtime import _locate_executable, _run, normalize_command_output
from boundary_schema import load_schema
from boundary_schema_validation import validate_boundary
from boundary_types import BoundaryError
from verification_engine import verify_change_set
from verification_git import collect_git_changes
from verification_types import VerificationError

_FAIL_ON = ("never", "error", "blocking")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify actual Git changes against a planned "
            "SpecDD Change Boundary."
        )
    )
    parser.add_argument(
        "--root",
        help="Repository root; defaults to repository discovery",
    )
    parser.add_argument("--boundary", required=True, help="Planned Change Boundary JSON path")
    parser.add_argument(
        "--feature-dir",
        required=True,
        help=(
            "Active Spec Kit feature directory; its artifacts "
            "are excluded from implementation writes"
        ),
    )
    parser.add_argument("--feature", help="Expected active feature identifier")
    parser.add_argument("--schema", help="Override the Change Boundary schema path")
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
            "severity threshold is present"
        ),
    )
    return parser.parse_args(argv)


def _root_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _load_boundary(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(f"Change Boundary was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"Change Boundary is invalid JSON: {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise VerificationError(f"Change Boundary root must be an object: {path}")
    return value


def _empty_actual(planned: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "feature": planned["feature"],
        "targets": [],
        "authorities": [],
        "crossBoundary": False,
        "unresolved": [],
        "generation": planned["generation"],
    }


def _specdd_lint(root: Path, executable: str) -> dict[str, Any]:
    command = _locate_executable(executable)
    result = _run([command, "lint"], root, subprocess.run)
    return {
        "exitCode": result.returncode,
        "stdout": normalize_command_output(root, result.stdout),
        "stderr": normalize_command_output(root, result.stderr),
    }


def _serialize(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"


def _write_output(root: Path, value: Mapping[str, Any], output: str) -> None:
    rendered = _serialize(value)
    if output == "-":
        sys.stdout.write(rendered)
        return

    output_path = _root_path(root, output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=output_path.parent,
        prefix=output_path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)

    try:
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)


def _result_exit_code(result: Mapping[str, Any], fail_on: str) -> int:
    if fail_on == "never":
        return 0

    summary = result.get("summary", {})
    counts = (
        summary.get("countsBySeverity", {})
        if isinstance(summary, Mapping)
        else {}
    )
    if not isinstance(counts, Mapping):
        return 0
    if fail_on == "blocking":
        return 1 if counts.get("blocking", 0) else 0
    return 1 if counts.get("error", 0) or counts.get("blocking", 0) else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        schema = load_schema(root, args.schema)
        planned = _load_boundary(_root_path(root, args.boundary))
        validate_boundary(planned, schema)

        changes = collect_git_changes(root, feature_dir=args.feature_dir)
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
            actual = _empty_actual(planned)
            validate_boundary(actual, schema)

        result = verify_change_set(
            planned,
            actual,
            changes,
            lint=_specdd_lint(root, args.specdd),
            expected_feature=args.feature,
        )
        _write_output(root, result, args.output)
        return _result_exit_code(result, args.fail_on)
    except (BoundaryError, VerificationError, OSError) as exc:
        print(f"verification.py: {exc}", file=sys.stderr)
        return 2
