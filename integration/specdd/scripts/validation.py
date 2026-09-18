#!/usr/bin/env python3
"""Validate Spec Kit task scope against a SpecDD Change Boundary."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SCRIPT_DIR),
    )

from validation_cli import (  # noqa: E402,F401
    _result_exit_code,
    main,
    parse_args,
)
from validation_engine import (  # noqa: E402,F401
    SEVERITIES,
    VALID_STAGES,
    validate_feature,
)
from validation_permissions import (  # noqa: E402,F401
    project_task_modification_permissions,
    requires_permission_projection,
)
from validation_tasks import (  # noqa: E402,F401
    extract_repository_targets,
    parse_tasks,
    parse_tasks_file,
)
from validation_types import (  # noqa: E402,F401
    TaskRecord,
    ValidationError,
)


if __name__ == "__main__":
    raise SystemExit(main())
