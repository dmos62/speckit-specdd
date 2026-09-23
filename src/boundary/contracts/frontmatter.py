"""Parser for Boundary v1 contract frontmatter."""

from dataclasses import dataclass
import ast
import re

from .errors import ContractParseError
from .scopes import normalize_contract_scope

_SCHEMA = "boundary.contract/v1"
_SCALAR_FIELDS = {"schema", "id"}
_LIST_FIELDS = {"owns", "applies_to", "depends_on"}
_KNOWN_FIELDS = _SCALAR_FIELDS | _LIST_FIELDS
_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:[ \t]*(.*))?$")
_LIST_ITEM_RE = re.compile(r"^[ \t]+-[ \t]+(.+?)\s*$")


@dataclass(frozen=True, slots=True)
class ParsedFrontmatter:
    """Validated deterministic fields from one native contract."""

    contract_id: str
    owns: tuple[str, ...]
    applies_to: tuple[str, ...]
    depends_on: tuple[str, ...]


def parse_frontmatter(source: str) -> tuple[ParsedFrontmatter, str]:
    """Parse Boundary v1 YAML-frontmatter subset and return the Markdown body."""

    lines = source.split("\n")
    if not lines or lines[0] != "---":
        raise ContractParseError("contract must start with YAML frontmatter")

    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ContractParseError("contract frontmatter is missing closing '---'") from exc

    values = _parse_fields(lines[1:end])
    schema = values.get("schema")
    contract_id = values.get("id")
    if schema != _SCHEMA:
        raise ContractParseError(f"schema must be {_SCHEMA!r}")
    if not isinstance(contract_id, str) or not contract_id:
        raise ContractParseError("contract id must be a non-empty string")

    owns = _scope_values(values, "owns")
    applies_to = _scope_values(values, "applies_to")
    if not owns and not applies_to:
        raise ContractParseError(
            "contract must declare at least one owns or applies_to scope"
        )

    depends_on = _string_list(values, "depends_on")
    body = "\n".join(lines[end + 1 :])
    return ParsedFrontmatter(contract_id, owns, applies_to, depends_on), body


def _parse_fields(lines: list[str]) -> dict[str, str | list[str]]:
    values: dict[str, str | list[str]] = {}
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if raw[:1].isspace():
            raise ContractParseError(
                f"unexpected indented frontmatter at line {index + 2}"
            )

        match = _FIELD_RE.match(raw)
        if match is None:
            raise ContractParseError(f"invalid frontmatter at line {index + 2}")
        key, raw_value = match.groups()
        if key not in _KNOWN_FIELDS:
            raise ContractParseError(f"unknown frontmatter field {key!r}")
        if key in values:
            raise ContractParseError(f"duplicate frontmatter field {key!r}")

        value = _strip_inline_comment(raw_value or "").strip()
        if key in _SCALAR_FIELDS:
            if not value:
                raise ContractParseError(
                    f"frontmatter field {key!r} requires a value"
                )
            values[key] = _parse_string(value)
            index += 1
            continue

        if value:
            values[key] = _parse_inline_list(value, key)
            index += 1
            continue

        items: list[str] = []
        index += 1
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                index += 1
                continue
            if not candidate[:1].isspace():
                break
            item_match = _LIST_ITEM_RE.match(candidate)
            if item_match is None:
                raise ContractParseError(
                    f"frontmatter field {key!r} requires a flat string list"
                )
            item = _strip_inline_comment(item_match.group(1)).strip()
            if not item:
                raise ContractParseError(
                    f"frontmatter field {key!r} contains an empty item"
                )
            items.append(_parse_string(item))
            index += 1
        values[key] = items

    return values


def _parse_inline_list(value: str, key: str) -> list[str]:
    if value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        raise ContractParseError(f"frontmatter field {key!r} must be an array")

    inner = value[1:-1].strip()
    if not inner:
        return []
    return [_parse_string(part) for part in _split_inline_items(inner, key)]


def _split_inline_items(value: str, key: str) -> list[str]:
    items: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "," and quote is None:
            item = value[start:index].strip()
            if not item:
                raise ContractParseError(
                    f"frontmatter field {key!r} contains an empty item"
                )
            items.append(item)
            start = index + 1
    if quote is not None:
        raise ContractParseError(
            f"frontmatter field {key!r} contains an unterminated quote"
        )
    item = value[start:].strip()
    if not item:
        raise ContractParseError(
            f"frontmatter field {key!r} contains an empty item"
        )
    items.append(item)
    return items


def _parse_string(value: str) -> str:
    if value[:1] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ContractParseError("invalid quoted frontmatter string") from exc
        if not isinstance(parsed, str):
            raise ContractParseError("frontmatter values must be strings")
        value = parsed
    if not value:
        raise ContractParseError("frontmatter values must be non-empty strings")
    return value


def _strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if (
            char == "#"
            and quote is None
            and (index == 0 or value[index - 1].isspace())
        ):
            return value[:index]
    return value


def _scope_values(
    values: dict[str, str | list[str]],
    key: str,
) -> tuple[str, ...]:
    return tuple(
        normalize_contract_scope(value)
        for value in _string_list(values, key)
    )


def _string_list(
    values: dict[str, str | list[str]],
    key: str,
) -> tuple[str, ...]:
    value = values.get(key, [])
    if not isinstance(value, list):
        raise ContractParseError(f"frontmatter field {key!r} must be an array")
    return tuple(value)
