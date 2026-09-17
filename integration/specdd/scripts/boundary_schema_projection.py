from __future__ import annotations

from typing import Any, Mapping

from boundary_schema import _resolve_ref, _resolved_schema_rule
from boundary_types import BoundaryError, Unresolved


def _generation_metadata(
    schema: Mapping[str, Any],
    cli: str,
    framework: str,
) -> tuple[str, dict[str, str]] | None:
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return None

    base = {
        "schemaVersion",
        "feature",
        "targets",
        "authorities",
        "crossBoundary",
        "unresolved",
    }

    for name, rule in properties.items():
        if name in base or not isinstance(rule, Mapping):
            continue

        metadata_rule = rule
        if isinstance(rule.get("$ref"), str):
            metadata_rule = _resolve_ref(
                schema,
                rule["$ref"],
            )

        child_properties = metadata_rule.get("properties")
        if not isinstance(child_properties, Mapping):
            continue

        values: dict[str, str] = {}
        for child in child_properties:
            lower = str(child).lower()
            if "framework" in lower:
                values[str(child)] = framework
            elif (
                "cli" in lower
                or lower
                in {
                    "specdd",
                    "specddversion",
                    "toolversion",
                }
            ):
                values[str(child)] = cli

        required = (
            set(metadata_rule.get("required", []))
            if isinstance(
                metadata_rule.get("required"),
                list,
            )
            else set()
        )

        if required.issubset(values) and values:
            return str(name), values

    return None


def _matching_property(
    names: list[str],
    exact: str,
    tokens: tuple[str, ...],
) -> str | None:
    for name in names:
        if name.lower() == exact:
            return name

    for name in names:
        lower = name.lower()
        if all(token in lower for token in tokens):
            return name

    return None


def _unresolved_record(
    item: Unresolved,
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        raise BoundaryError(
            "Change Boundary schema does not define unresolved entries"
        )

    unresolved_rule = properties.get("unresolved", {})
    if not isinstance(unresolved_rule, Mapping):
        raise BoundaryError(
            "Change Boundary schema does not define unresolved entries"
        )
    unresolved_rule = _resolved_schema_rule(
        schema,
        unresolved_rule,
    )

    item_rule = unresolved_rule.get("items")
    if not isinstance(item_rule, Mapping):
        raise BoundaryError(
            "Change Boundary schema does not define unresolved item fields"
        )
    item_rule = _resolved_schema_rule(
        schema,
        item_rule,
    )

    item_properties = item_rule.get("properties")
    if not isinstance(item_properties, Mapping):
        raise BoundaryError(
            "Change Boundary schema does not define unresolved item properties"
        )

    names = [str(name) for name in item_properties]

    input_name = _matching_property(
        names,
        "input",
        ("input",),
    )
    if input_name is None:
        input_name = _matching_property(
            names,
            "",
            ("original",),
        )

    message_name = _matching_property(
        names,
        "message",
        ("message",),
    )
    if message_name is None:
        for token in (
            "reason",
            "error",
            "diagnostic",
            "detail",
        ):
            message_name = _matching_property(
                names,
                token,
                (token,),
            )
            if message_name is not None:
                break

    path_name = _matching_property(
        names,
        "path",
        ("path",),
    )
    if path_name is None:
        path_name = _matching_property(
            names,
            "",
            ("normalized",),
        )

    code_name = _matching_property(
        names,
        "code",
        ("code",),
    )
    authorities_name = _matching_property(
        names,
        "candidateauthorities",
        ("candidate", "author"),
    )

    if input_name is None or message_name is None:
        raise BoundaryError(
            "Change Boundary schema has unrecognized unresolved-entry fields"
        )

    result: dict[str, Any] = {
        input_name: item.input,
        message_name: item.message,
    }

    if code_name is not None:
        result[code_name] = item.code

    if item.path is not None and path_name is not None:
        result[path_name] = item.path

    if (
        item.candidate_authorities
        and authorities_name is not None
    ):
        result[authorities_name] = list(
            item.candidate_authorities
        )

    return result
