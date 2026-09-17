from __future__ import annotations

import json
import re
from typing import Any, Mapping

from boundary_schema import (
    ANNOTATION_SCHEMA_KEYS,
    _resolve_ref,
    _type_matches,
)
from boundary_types import BoundaryError


def _schema_errors(
    value: Any,
    rule: Mapping[str, Any],
    schema: Mapping[str, Any],
    path: str,
) -> list[str]:
    errors: list[str] = []
    supported = ANNOTATION_SCHEMA_KEYS | {
        "$ref",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "else",
        "enum",
        "if",
        "items",
        "maxItems",
        "maxLength",
        "maxProperties",
        "minItems",
        "minLength",
        "minProperties",
        "not",
        "oneOf",
        "pattern",
        "patternProperties",
        "properties",
        "required",
        "then",
        "type",
        "uniqueItems",
    }

    unknown = set(rule) - supported
    if unknown:
        raise BoundaryError(
            "Unsupported JSON Schema keyword(s): "
            + ", ".join(sorted(unknown))
        )

    if "$ref" in rule:
        errors.extend(
            _schema_errors(
                value,
                _resolve_ref(schema, str(rule["$ref"])),
                schema,
                path,
            )
        )

    for child in rule.get("allOf", []):
        if isinstance(child, Mapping):
            errors.extend(_schema_errors(value, child, schema, path))

    if isinstance(rule.get("anyOf"), list):
        choices = [
            child
            for child in rule["anyOf"]
            if isinstance(child, Mapping)
        ]
        if choices and not any(
            not _schema_errors(value, child, schema, path)
            for child in choices
        ):
            errors.append(f"{path}: does not match any allowed schema")

    if isinstance(rule.get("oneOf"), list):
        choices = [
            child
            for child in rule["oneOf"]
            if isinstance(child, Mapping)
        ]
        if (
            sum(
                not _schema_errors(value, child, schema, path)
                for child in choices
            )
            != 1
        ):
            errors.append(
                f"{path}: must match exactly one allowed schema"
            )

    if (
        isinstance(rule.get("not"), Mapping)
        and not _schema_errors(value, rule["not"], schema, path)
    ):
        errors.append(f"{path}: matches a forbidden schema")

    if isinstance(rule.get("if"), Mapping):
        condition = not _schema_errors(
            value,
            rule["if"],
            schema,
            path,
        )
        branch = rule.get("then" if condition else "else")
        if isinstance(branch, Mapping):
            errors.extend(
                _schema_errors(
                    value,
                    branch,
                    schema,
                    path,
                )
            )

    if "const" in rule and value != rule["const"]:
        errors.append(f"{path}: expected {rule['const']!r}")

    if isinstance(rule.get("enum"), list) and value not in rule["enum"]:
        errors.append(f"{path}: value is not in the allowed enum")

    expected = rule.get("type")
    types = (
        [expected]
        if isinstance(expected, str)
        else expected
        if isinstance(expected, list)
        else []
    )
    if types and not any(
        isinstance(item, str) and _type_matches(value, item)
        for item in types
    ):
        errors.append(f"{path}: wrong type")
        return errors

    if isinstance(value, Mapping):
        errors.extend(_object_errors(value, rule, schema, path))

    if isinstance(value, list):
        errors.extend(_array_errors(value, rule, schema, path))

    if isinstance(value, str):
        errors.extend(_string_errors(value, rule, path))

    return errors


def _object_errors(
    value: Mapping[str, Any],
    rule: Mapping[str, Any],
    schema: Mapping[str, Any],
    path: str,
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

    pattern_properties = rule.get("patternProperties", {})
    pattern_properties = (
        pattern_properties
        if isinstance(pattern_properties, Mapping)
        else {}
    )

    for key, item in value.items():
        matched = False
        child = properties.get(key)

        if isinstance(child, Mapping):
            matched = True
            errors.extend(
                _schema_errors(
                    item,
                    child,
                    schema,
                    f"{path}.{key}",
                )
            )

        for pattern, pattern_rule in pattern_properties.items():
            if (
                isinstance(pattern_rule, Mapping)
                and re.search(str(pattern), str(key))
            ):
                matched = True
                errors.extend(
                    _schema_errors(
                        item,
                        pattern_rule,
                        schema,
                        f"{path}.{key}",
                    )
                )

        if not matched and rule.get("additionalProperties") is False:
            errors.append(
                f"{path}: unexpected property {key!r}"
            )
        elif (
            not matched
            and isinstance(rule.get("additionalProperties"), Mapping)
        ):
            errors.extend(
                _schema_errors(
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
                _schema_errors(
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


def validate_boundary(
    value: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    """Validate output against the checked-in schema without a runtime dependency."""
    errors = _schema_errors(value, schema, schema, "$")
    if errors:
        detail = "; ".join(errors[:8])
        if len(errors) > 8:
            detail += f"; and {len(errors) - 8} more"
        raise BoundaryError(
            "Generated Change Boundary does not satisfy its schema: "
            + detail
        )
