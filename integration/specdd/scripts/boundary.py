#!/usr/bin/env python3
"""Build a derived SpecDD Change Boundary from the real SpecDD resolver."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SCRIPT_DIR),
    )

from boundary_builder import (  # noqa: E402,F401
    boundary_context_evidence_path,
    boundary_fingerprint,
    build_change_boundary,
    load_boundary_context_evidence,
    serialize_boundary,
    write_boundary,
    write_boundary_context_evidence,
)
from boundary_cli import (  # noqa: E402,F401
    main,
    parse_args,
)
from boundary_paths import (  # noqa: E402,F401
    _expand_braces,
    _glob_matches,
    _glob_regex,
    _ownership_matches,
    _path_entry,
    _resolve_specdd_path,
    _windows_absolute,
    discover_repository_root,
    normalize_resolver_path,
    normalize_target,
    resolve_root,
)
from boundary_runtime import (  # noqa: E402,F401
    _locate_executable,
    _package_version,
    _run,
    framework_version,
    specdd_cli_version,
)
from boundary_schema import (  # noqa: E402,F401
    ANNOTATION_SCHEMA_KEYS,
    SCHEMA_RELATIVE_PATH,
    _resolve_ref,
    _resolved_schema_rule,
    _type_matches,
    load_schema,
)
from boundary_schema_projection import (  # noqa: E402,F401
    _generation_metadata,
    _unresolved_record,
)
from boundary_schema_validation import (  # noqa: E402,F401
    _schema_errors,
    validate_boundary,
)
from boundary_specdd import (  # noqa: E402,F401
    _section_body,
    derive_primary_authority,
    extract_resolved_specs,
    resolve_target,
    specdd_context_fingerprint,
)
from boundary_types import (  # noqa: E402,F401
    BoundaryError,
    RunCommand,
    Target,
    Unresolved,
)


if __name__ == "__main__":
    raise SystemExit(main())
