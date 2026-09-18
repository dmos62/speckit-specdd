#!/usr/bin/env python3
"""Verify actual Git writes against the authorized SpecDD authority snapshot."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SCRIPT_DIR),
    )

from verification_cli import (  # noqa: E402,F401
    _result_exit_code,
    main,
    parse_args,
)
from verification_engine import (  # noqa: E402,F401
    verify_change_set,
)
from verification_git import (  # noqa: E402,F401
    authorization_snapshot_path,
    collect_git_changes,
    write_authorization_snapshot,
)
from verification_types import (  # noqa: E402,F401
    ChangeSet,
    GitChange,
    VerificationError,
)


if __name__ == "__main__":
    raise SystemExit(main())
