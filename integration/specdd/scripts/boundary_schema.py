from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from boundary_types import BoundaryError

SCHEMA_RELATIVE_PATH = Path(
    "integration/specdd/schemas/change-boundary.schema.json"
)
BUNDLED_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "change-boundary.schema.json"
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
SchemaVisitor = Callable[
    [Any, Mapping[str, Any], Mapping[str, Any], str],
    list[str],
]


def load_schema(
    root: Path,
    override: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    if override is not None:
        path = Path(override).expanduser()
        candidates = [path if path.is_absolute() else root / path]
    else:
        candidates = [BUNDLED_SCHEMA_PATH]
        canonical = root / SCHEMA_RELATIVE_PATH
        if canonical.resolve(strict=False) != BUNDLED_SCHEMA_PATH:
            candidates.append(canonical)

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


def _object_errors(
    value: Mapping[str, Any],
    rule: Mapping[str, Any],
    schema: Mapping[str, Any],
    path: str,
    visit: SchemaVisitor,
) -> list[str]:
    errors: list[str] = []
    required = rule.get("required", [])

    if isinstance(required, list):
        errors.extend(
            f"{path}: missing required property {key!r}"
            for key in required
            if key not in value
        )

    if (
        isinstance(rule.get("minProperties"), int)
        and len(value) < rule["minProperties"]
    ):
        errors.append(f"{path}: too few properties")

    if (
        isinstance(rule.get("maxProperties"), int)
        and len(value) > rule["maxProperties"]
    ):
        errors.append(f"{path}: too many properties")

    properties = rule.get("properties", {})
    properties = properties if isinstance(properties, Mapping) else {}
    patterns = rule.get("patternProperties", {})
    patterns = patterns if isinstance(patterns, Mapping) else {}

    for key, item in value.items():
        matched = False
        child = properties.get(key)

        if isinstance(child, Mapping):
            matched = True
            errors.extend(
                visit(
                    item,
                    child,
                    schema,
                    f"{path}.{key}",
                )
            )

        for pattern, pattern_rule in patterns.items():
            if (
                isinstance(pattern_rule, Mapping)
                and re.search(str(pattern), str(key))
            ):
                matched = True
                errors.extend(
                    visit(
                        item,
                        pattern_rule,
                        schema,
                        f"{path}.{key}",
                    )
                )

        if not matched and rule.get("additionalProperties") is False:
            errors.append(f"{path}: unexpected property {key!r}")
        elif (
            not matched
            and isinstance(rule.get("additionalProperties"), Mapping)
        ):
            errors.extend(
                visit(
                    item,
                    rule["additionalProperties"],
                    schema,
                    f"{path}.{key}",
                )
            )

    return errors


def _array_errors(
    value: list[Any],
    rule: Mapping[str, Any],
    schema: Mapping[str, Any],
    path: str,
    visit: SchemaVisitor,
) -> list[str]:
    errors: list[str] = []

    if (
        isinstance(rule.get("minItems"), int)
        and len(value) < rule["minItems"]
    ):
        errors.append(f"{path}: too few items")

    if (
        isinstance(rule.get("maxItems"), int)
        and len(value) > rule["maxItems"]
    ):
        errors.append(f"{path}: too many items")

    if rule.get("uniqueItems") is True:
        encoded = [
            json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
            )
            for item in value
        ]
        if len(encoded) != len(set(encoded)):
            errors.append(f"{path}: items must be unique")

    if isinstance(rule.get("items"), Mapping):
        for index, item in enumerate(value):
            errors.extend(
                visit(
                    item,
                    rule["items"],
                    schema,
                    f"{path}[{index}]",
                )
            )

    return errors


def _string_errors(
    value: str,
    rule: Mapping[str, Any],
    path: str,
) -> list[str]:
    errors: list[str] = []

    if (
        isinstance(rule.get("minLength"), int)
        and len(value) < rule["minLength"]
    ):
        errors.append(f"{path}: string is too short")

    if (
        isinstance(rule.get("maxLength"), int)
        and len(value) > rule["maxLength"]
    ):
        errors.append(f"{path}: string is too long")

    if (
        isinstance(rule.get("pattern"), str)
        and re.search(rule["pattern"], value) is None
    ):
        errors.append(
            f"{path}: string does not match {rule['pattern']!r}"
        )

    return errors
