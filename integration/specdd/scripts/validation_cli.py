from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from boundary_paths import resolve_root
from boundary_schema import load_schema
from boundary_schema_validation import validate_boundary
from boundary_types import BoundaryError
from validation_engine import VALID_STAGES, validate_feature
from validation_permissions import (
    project_task_modification_permissions,
    requires_permission_projection,
)
from validation_tasks import parse_tasks_file
from validation_types import ValidationError

_FAIL_ON = ("never", "error", "blocking")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Spec Kit task write targets against "
            "a derived SpecDD Change Boundary."
        )
    )
    parser.add_argument(
        "--root",
        help="Repository root; defaults to repository discovery",
    )
    parser.add_argument("--boundary", required=True, help="Change Boundary JSON path")
    parser.add_argument("--tasks", required=True, help="Spec Kit tasks.md path")
    parser.add_argument("--feature", help="Expected active feature identifier")
    parser.add_argument(
        "--stage",
        choices=sorted(VALID_STAGES),
        default="tasks",
        help="Lifecycle strictness stage (default: tasks)",
    )
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


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"{label} was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{label} is invalid JSON: {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise ValidationError(f"{label} root must be an object: {path}")
    return value


def _serialize(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


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
    counts = summary.get("countsBySeverity", {}) if isinstance(summary, Mapping) else {}
    if not isinstance(counts, Mapping):
        return 0
    if fail_on == "blocking":
        return 1 if counts.get("blocking", 0) else 0
    return 1 if counts.get("error", 0) or counts.get("blocking", 0) else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        boundary_path = _root_path(root, args.boundary)
        tasks_path = _root_path(root, args.tasks)
        boundary = _load_object(boundary_path, label="Change Boundary")
        schema = load_schema(root, args.schema)
        validate_boundary(boundary, schema)

        if not tasks_path.is_file():
            raise ValidationError(f"Spec Kit task file was not found: {tasks_path}")

        tasks = parse_tasks_file(root, tasks_path)
        permissions = {}
        if requires_permission_projection(boundary, tasks):
            permissions = project_task_modification_permissions(
                root,
                boundary,
                tasks,
                executable=args.specdd,
            )
        result = validate_feature(
            boundary,
            tasks,
            stage=args.stage,
            expected_feature=args.feature,
            task_permissions=permissions,
        )
        _write_output(root, result, args.output)
        return _result_exit_code(result, args.fail_on)
    except (BoundaryError, ValidationError, OSError) as exc:
        print(f"validation.py: {exc}", file=sys.stderr)
        return 2
