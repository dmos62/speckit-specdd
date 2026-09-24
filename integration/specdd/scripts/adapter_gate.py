#!/usr/bin/env python3
"""Run native Boundary transitions for the concrete Spec Kit adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
SPECIFY_ROOT = SCRIPT_DIR.parents[2]
RUNTIME_ROOT = SPECIFY_ROOT / "boundary-runtime"
if RUNTIME_ROOT.is_dir() and str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from boundary.authorization import AuthorizationError  # noqa: E402
from boundary.verification import VerificationError  # noqa: E402
from spec_kit_adapter import (  # noqa: E402
    SpecKitAdapterError,
    active_feature,
    authorize_feature,
    resolve_repository_root,
    verify_feature,
)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Boundary transitions for the Spec Kit adapter."
    )
    parser.add_argument(
        "stage",
        choices=("authorize", "verify"),
    )
    parser.add_argument(
        "--root",
        help="Repository root; defaults to Git discovery.",
    )
    return parser.parse_args(argv)


def run_stage(root: Path, stage: str) -> dict[str, object]:
    """Run one adapter lifecycle transition and return stable JSON output."""

    feature_dir, feature_path = active_feature(root)
    if stage == "authorize":
        record = authorize_feature(root, feature_dir)
    else:
        record = verify_feature(root, feature_dir)

    return {
        "adapter": "speckit",
        "feature": feature_path,
        "operation": record.to_document(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_repository_root(args.root)
        value = run_stage(root, args.stage)
    except (
        AuthorizationError,
        VerificationError,
        SpecKitAdapterError,
        OSError,
        ValueError,
    ) as exc:
        print(f"boundary Spec Kit adapter: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
