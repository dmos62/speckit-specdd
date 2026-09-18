#!/usr/bin/env python3
"""Verify actual Git writes against the authorized SpecDD authority snapshot."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verification_cli import (  # noqa: E402,F401
    _result_exit_code,
    main,
    parse_args,
)
from verification_engine import verify_change_set  # noqa: E402,F401
from verification_git import (  # noqa: E402,F401
    authorization_snapshot_path,
    authorization_spec_plan_path,
    collect_git_changes,
    load_authorization_plan,
    write_authorization_evidence,
)
from verification_types import (  # noqa: E402,F401
    CONTROL_SELECTION_SOURCES,
    EDITABLE_BOOTSTRAP_CONTROLS,
    IMMUTABLE_BOOTSTRAP_CONTROL,
    LOCAL_BOOTSTRAP_CONTROL,
    PROJECT_BOOTSTRAP_CONTROL,
    ChangeSet,
    GitChange,
    VerificationError,
)


if __name__ == "__main__":
    raise SystemExit(main())
