from __future__ import annotations

import argparse
import sys
from typing import Sequence

from boundary_builder import (
    build_change_boundary,
    write_boundary,
    write_boundary_context_evidence,
)
from boundary_paths import resolve_root
from boundary_schema import load_schema
from boundary_types import BoundaryError


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Project repository targets into a Change Boundary v1 document. "
            "When the installed SpecDD resolver exposes typed intended-target "
            "support, non-existent targets are resolved without probe files."
        )
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help=(
            "Existing or intended target paths; missing paths default to "
            "ordinary files, a trailing separator marks a folder, and "
            "a .sdd suffix marks a specification target"
        ),
    )
    parser.add_argument(
        "--root",
        help="Resolution root; defaults to the discovered repository root",
    )
    parser.add_argument(
        "--feature",
        help="Feature identifier; defaults to the root directory name",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Output path, or '-' for stdout (default)",
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
        "--record-context-evidence",
        action="store_true",
        help=(
            "Record fingerprint-bound effective SpecDD context in current-"
            "worktree Git metadata for later authorization freshness checks"
        ),
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(argv)

    try:
        root = resolve_root(args.root)
        schema = load_schema(root, args.schema)
        context_fingerprints: dict[str, str] = {}
        value = build_change_boundary(
            root,
            args.targets,
            feature=args.feature or root.name,
            schema=schema,
            executable=args.specdd,
            context_fingerprints=context_fingerprints,
        )
        if args.record_context_evidence:
            write_boundary_context_evidence(
                root,
                value,
                context_fingerprints,
            )
        write_boundary(value, args.output)
    except BoundaryError as exc:
        print(f"boundary.py: {exc}", file=sys.stderr)
        return 2

    return 0
