from __future__ import annotations

from typing import Any, Mapping

from boundary_schema import (
    ANNOTATION_SCHEMA_KEYS,
    _array_errors,
    _object_errors,
    _resolve_ref,
    _string_errors,
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
        matches = sum(
            not _schema_errors(value, child, schema, path)
            for child in choices
        )
        if matches != 1:
            errors.append(
                f"{path}: must match exactly one allowed schema"
            )

    if (
        isinstance(rule.get("not"), Mapping)
        and not _schema_errors(
            value,
            rule["not"],
            schema,
            path,
        )
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
        errors.extend(
            _object_errors(
                value,
                rule,
                schema,
                path,
                _schema_errors,
            )
        )

    if isinstance(value, list):
        errors.extend(
            _array_errors(
                value,
                rule,
                schema,
                path,
                _schema_errors,
            )
        )

    if isinstance(value, str):
        errors.extend(_string_errors(value, rule, path))

    return errors


def _semantic_errors(
    value: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    targets = value.get("targets")
    if not isinstance(targets, list):
        return errors

    paths: set[str] = set()
    projected_authorities: set[str] = set()

    for index, item in enumerate(targets):
        if not isinstance(item, Mapping):
            continue

        path = item.get("path")
        if isinstance(path, str):
            if path in paths:
                errors.append(
                    f"$.targets[{index}].path: duplicate target path {path!r}"
                )
            paths.add(path)

        authority = item.get("primaryAuthority")
        if isinstance(authority, str):
            projected_authorities.add(authority)
            resolved_specs = item.get("resolvedSpecs")
            if (
                isinstance(resolved_specs, list)
                and authority not in resolved_specs
            ):
                errors.append(
                    f"$.targets[{index}].primaryAuthority: {authority!r} "
                    "is not present in resolvedSpecs"
                )

    authorities = value.get("authorities")
    if (
        isinstance(authorities, list)
        and all(isinstance(item, str) for item in authorities)
        and set(authorities) != projected_authorities
    ):
        errors.append(
            "$.authorities: must equal the distinct non-null target "
            "primaryAuthority values"
        )

    cross_boundary = value.get("crossBoundary")
    if (
        isinstance(cross_boundary, bool)
        and cross_boundary != (len(projected_authorities) > 1)
    ):
        errors.append(
            "$.crossBoundary: must agree with the projected authority set"
        )

    unresolved = value.get("unresolved")
    if not isinstance(unresolved, list):
        return errors

    for index, item in enumerate(unresolved):
        if not isinstance(item, Mapping):
            continue

        path = item.get("normalizedPath")
        if isinstance(path, str) and path in paths:
            errors.append(
                f"$.unresolved[{index}].normalizedPath: {path!r} also "
                "appears in resolved targets"
            )

        code = item.get("code")
        candidates = item.get("candidateAuthorities")
        candidate_values = (
            candidates
            if isinstance(candidates, list)
            else []
        )

        if (
            code == "AMBIGUOUS_AUTHORITY"
            and len(candidate_values) < 2
        ):
            errors.append(
                f"$.unresolved[{index}].candidateAuthorities: "
                "AMBIGUOUS_AUTHORITY requires at least two candidates"
            )
        elif (
            code != "AMBIGUOUS_AUTHORITY"
            and candidate_values
        ):
            errors.append(
                f"$.unresolved[{index}].candidateAuthorities: candidates "
                "are valid only for AMBIGUOUS_AUTHORITY"
            )

    return errors


def _raise_errors(
    prefix: str,
    errors: list[str],
) -> None:
    detail = "; ".join(errors[:8])
    if len(errors) > 8:
        detail += f"; and {len(errors) - 8} more"
    raise BoundaryError(prefix + detail)


def validate_boundary(
    value: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    """Validate Change Boundary shape and deterministic cross-field invariants."""
    schema_errors = _schema_errors(value, schema, schema, "$")
    if schema_errors:
        _raise_errors(
            "Generated Change Boundary does not satisfy its schema: ",
            schema_errors,
        )

    semantic_errors = _semantic_errors(value)
    if semantic_errors:
        _raise_errors(
            "Change Boundary is semantically inconsistent: ",
            semantic_errors,
        )
