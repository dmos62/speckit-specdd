from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from boundary_types import BoundaryError

SCHEMA_RELATIVE_PATH = Path(
    "integration/specdd/schemas/change-boundary.schema.json"
)
ANNOTATION_SCHEMA_KEYS = {
    "$comment",
    "$id",
    "$schema",
    "$defs",
    "default",
    "description",
    "examples",
    "format",
    "title",
}


def load_schema(
    root: Path,
    override: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    if override is not None:
        path = Path(override).expanduser()
        candidates = [path if path.is_absolute() else root / path]
    else:
        candidates = [root / SCHEMA_RELATIVE_PATH]
        source_root = Path(__file__).resolve().parents[3]
        if source_root != root:
            candidates.append(source_root / SCHEMA_RELATIVE_PATH)

    path = next(
        (candidate for candidate in candidates if candidate.is_file()),
        candidates[0],
    )

    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BoundaryError(
            "Change Boundary schema was not found; searched: "
            + ", ".join(str(candidate) for candidate in candidates)
        ) from exc
    except json.JSONDecodeError as exc:
        raise BoundaryError(
            f"Change Boundary schema is invalid JSON: {path}: {exc}"
        ) from exc

    if not isinstance(schema, dict):
        raise BoundaryError(
            f"Change Boundary schema root must be an object: {path}"
        )

    return schema


def _resolve_ref(
    schema: Mapping[str, Any],
    ref: str,
) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        raise BoundaryError(
            f"Unsupported external JSON Schema reference: {ref}"
        )

    current: Any = schema
    for encoded in ref[2:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or token not in current:
            raise BoundaryError(
                f"Unresolvable JSON Schema reference: {ref}"
            )
        current = current[token]

    if not isinstance(current, Mapping):
        raise BoundaryError(
            f"JSON Schema reference does not resolve to an object: {ref}"
        )
    return current


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, Mapping)

    raise BoundaryError(f"Unsupported JSON Schema type: {expected}")


def _resolved_schema_rule(
    schema: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> Mapping[str, Any]:
    if isinstance(rule.get("$ref"), str):
        return _resolve_ref(schema, rule["$ref"])
    return rule
