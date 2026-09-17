#!/usr/bin/env python3
"""Build a derived SpecDD Change Boundary from the real SpecDD resolver."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence

SCHEMA_RELATIVE_PATH = Path("integration/specdd/schemas/change-boundary.schema.json")
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


class BoundaryError(RuntimeError):
    """The adapter cannot produce a valid Change Boundary."""


@dataclass(frozen=True)
class Target:
    raw: str
    path: str
    absolute_path: Path


@dataclass(frozen=True)
class Unresolved:
    input: str
    reason: str
    path: str | None = None


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def discover_repository_root(start: str | os.PathLike[str] | None = None) -> Path:
    start_path = Path(start or Path.cwd()).expanduser().resolve()
    if start_path.is_file():
        start_path = start_path.parent

    try:
        result = subprocess.run(
            ["git", "-C", str(start_path), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result = None

    if result is not None and result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()

    for candidate in (start_path, *start_path.parents):
        if (candidate / ".git").exists() or (candidate / ".specdd" / "bootstrap.md").is_file():
            return candidate

    raise BoundaryError(f"Could not discover a repository root from {start_path}")


def resolve_root(explicit_root: str | os.PathLike[str] | None) -> Path:
    root = Path(explicit_root).expanduser().resolve() if explicit_root else discover_repository_root()
    if not root.is_dir():
        raise BoundaryError(f"Repository root is not a directory: {root}")
    return root


def _windows_absolute(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", value)) or value.startswith("\\\\")


def normalize_target(root: Path, raw: str) -> Target:
    value = raw.strip()
    if not value:
        raise BoundaryError("Target path is empty")
    if os.name != "nt" and _windows_absolute(value):
        raise BoundaryError(f"Target uses an absolute Windows path on this host: {raw}")

    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root.joinpath(*PurePosixPath(value.replace("\\", "/")).parts)

    absolute = candidate.resolve(strict=False)
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise BoundaryError(f"Target is outside repository root: {raw}") from exc

    normalized = relative.as_posix()
    if normalized in {"", "."}:
        raise BoundaryError(f"Target must identify a path inside the repository: {raw}")

    return Target(raw=raw, path=normalized, absolute_path=absolute)


def normalize_resolver_path(root: Path, raw: str, *, spec: bool = False) -> str:
    value = raw.strip()
    if not value:
        raise BoundaryError("SpecDD resolver returned an empty path")

    if Path(value).is_absolute() or _windows_absolute(value):
        absolute = Path(value).resolve(strict=False)
        try:
            value = absolute.relative_to(root).as_posix()
        except ValueError as exc:
            raise BoundaryError(f"SpecDD resolver returned a path outside the root: {raw}") from exc
    else:
        value = value.replace("\\", "/")
        if value.startswith("./"):
            value = value[2:]
        parts = PurePosixPath(value).parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise BoundaryError(f"SpecDD resolver returned a non-normalized path: {raw}")
        value = PurePosixPath(*parts).as_posix()

    if value.startswith("/") or value.endswith("/") or "//" in value:
        raise BoundaryError(f"SpecDD resolver returned an invalid repository path: {raw}")
    if spec and not value.lower().endswith(".sdd"):
        raise BoundaryError(f"Resolved spec path does not end in .sdd: {raw}")

    return value


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

    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])

    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BoundaryError(
            "Change Boundary schema was not found; searched: "
            + ", ".join(str(candidate) for candidate in candidates)
        ) from exc
    except json.JSONDecodeError as exc:
        raise BoundaryError(f"Change Boundary schema is invalid JSON: {path}: {exc}") from exc

    if not isinstance(schema, dict):
        raise BoundaryError(f"Change Boundary schema root must be an object: {path}")

    return schema


def _resolve_ref(schema: Mapping[str, Any], ref: str) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        raise BoundaryError(f"Unsupported external JSON Schema reference: {ref}")

    current: Any = schema
    for encoded in ref[2:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or token not in current:
            raise BoundaryError(f"Unresolvable JSON Schema reference: {ref}")
        current = current[token]

    if not isinstance(current, Mapping):
        raise BoundaryError(f"JSON Schema reference does not resolve to an object: {ref}")

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
            "Unsupported JSON Schema keyword(s): " + ", ".join(sorted(unknown))
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
        choices = [child for child in rule["anyOf"] if isinstance(child, Mapping)]
        if choices and not any(
            not _schema_errors(value, child, schema, path)
            for child in choices
        ):
            errors.append(f"{path}: does not match any allowed schema")

    if isinstance(rule.get("oneOf"), list):
        choices = [child for child in rule["oneOf"] if isinstance(child, Mapping)]
        if sum(
            not _schema_errors(value, child, schema, path)
            for child in choices
        ) != 1:
            errors.append(f"{path}: must match exactly one allowed schema")

    if (
        isinstance(rule.get("not"), Mapping)
        and not _schema_errors(value, rule["not"], schema, path)
    ):
        errors.append(f"{path}: matches a forbidden schema")

    if isinstance(rule.get("if"), Mapping):
        condition = not _schema_errors(value, rule["if"], schema, path)
        branch = rule.get("then" if condition else "else")
        if isinstance(branch, Mapping):
            errors.extend(_schema_errors(value, branch, schema, path))

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
                    _schema_errors(item, child, schema, f"{path}.{key}")
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
                errors.append(f"{path}: unexpected property {key!r}")
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

    if isinstance(value, list):
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
                json.dumps(item, sort_keys=True, separators=(",", ":"))
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

    if isinstance(value, str):
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
            f"Generated Change Boundary does not satisfy its schema: {detail}"
        )


def _section_body(spec: Mapping[str, Any], name: str) -> list[str]:
    sections = spec.get("sections")
    if not isinstance(sections, Mapping):
        return []

    occurrences = sections.get(name)
    if not isinstance(occurrences, list):
        return []

    lines: list[str] = []
    for occurrence in occurrences:
        if not isinstance(occurrence, Mapping):
            continue
        body = occurrence.get("body")
        if isinstance(body, list):
            lines.extend(line for line in body if isinstance(line, str))

    return lines


def extract_resolved_specs(
    payload: Any,
    root: Path,
) -> list[dict[str, Any]]:
    if (
        not isinstance(payload, Mapping)
        or not isinstance(payload.get("directories"), list)
    ):
        raise BoundaryError(
            "SpecDD resolve JSON is missing the directories array"
        )

    specs: list[dict[str, Any]] = []
    seen: set[str] = set()

    for directory in payload["directories"]:
        if (
            not isinstance(directory, Mapping)
            or not isinstance(directory.get("specs"), list)
        ):
            raise BoundaryError(
                "SpecDD resolve JSON contains an invalid directory entry"
            )

        for raw_spec in directory["specs"]:
            if (
                not isinstance(raw_spec, Mapping)
                or not isinstance(raw_spec.get("path"), str)
            ):
                raise BoundaryError(
                    "SpecDD resolve JSON contains an invalid spec entry"
                )

            path = normalize_resolver_path(
                root,
                raw_spec["path"],
                spec=True,
            )
            if path in seen:
                continue

            seen.add(path)
            resolved_spec = dict(raw_spec)
            resolved_spec["path"] = path
            specs.append(resolved_spec)

    return specs


def _path_entry(line: str) -> str | None:
    text = line.strip()
    if not text.startswith(("./", "../", "/")):
        return None

    for index, character in enumerate(text):
        if character != ":" or index == 0 or text[index - 1].isspace():
            continue
        if index + 1 < len(text) and text[index + 1] == " ":
            return text[:index]

    return text


def _resolve_specdd_path(spec_path: str, candidate: str) -> str:
    path = (
        PurePosixPath(candidate.lstrip("/"))
        if candidate.startswith("/")
        else PurePosixPath(spec_path).parent / candidate
    )

    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise BoundaryError(
                    f"Ownership path escapes repository root: {candidate}"
                )
            parts.pop()
        else:
            parts.append(part)

    if not parts:
        raise BoundaryError(
            f"Ownership path resolves to the repository root: {candidate}"
        )

    return PurePosixPath(*parts).as_posix()


def _expand_braces(pattern: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", pattern)
    if match is None or "," not in match.group(1):
        return [pattern]

    results: list[str] = []
    for replacement in match.group(1).split(","):
        results.extend(
            _expand_braces(
                pattern[: match.start()]
                + replacement
                + pattern[match.end() :]
            )
        )

    return results


def _glob_regex(pattern: str) -> re.Pattern[str]:
    pieces = ["^"]
    index = 0

    while index < len(pattern):
        character = pattern[index]

        if character == "*":
            if (
                index + 1 < len(pattern)
                and pattern[index + 1] == "*"
            ):
                index += 2
                if index < len(pattern) and pattern[index] == "/":
                    pieces.append("(?:[^/]+/)*")
                    index += 1
                else:
                    pieces.append(".*")
                continue
            pieces.append("[^/]*")

        elif character == "?":
            pieces.append("[^/]")

        elif character == "[":
            closing = pattern.find("]", index + 1)
            if closing == -1:
                pieces.append(r"\[")
            else:
                content = pattern[index + 1 : closing]
                if content.startswith("!"):
                    pieces.append(
                        "[^" + re.escape(content[1:]) + "]"
                    )
                else:
                    pieces.append("[" + re.escape(content) + "]")
                index = closing

        else:
            pieces.append(re.escape(character))

        index += 1

    pieces.append("$")
    return re.compile("".join(pieces))


def _glob_matches(pattern: str, target: str) -> bool:
    return any(
        _glob_regex(expanded).fullmatch(target) is not None
        for expanded in _expand_braces(pattern)
    )


def _ownership_matches(
    root: Path,
    pattern: str,
    target: str,
) -> bool:
    if any(character in pattern for character in "*?[]{}"):
        return _glob_matches(pattern, target)

    if pattern == target:
        return True

    path = root.joinpath(*PurePosixPath(pattern).parts)
    return path.is_dir() and target.startswith(pattern.rstrip("/") + "/")


def derive_primary_authority(
    root: Path,
    target: str,
    specs: Sequence[Mapping[str, Any]],
) -> tuple[str | None, list[str]]:
    owners: list[str] = []

    for spec in specs:
        spec_path = str(spec["path"])

        for line in _section_body(spec, "Owns"):
            candidate = _path_entry(line)
            if candidate is None:
                continue

            try:
                resolved = _resolve_specdd_path(spec_path, candidate)
            except BoundaryError:
                continue

            if _ownership_matches(root, resolved, target):
                owners.append(spec_path)
                break

    owners = list(dict.fromkeys(owners))
    return (owners[0] if len(owners) == 1 else None, owners)


def _run(
    args: Sequence[str],
    root: Path,
    runner: RunCommand,
) -> subprocess.CompletedProcess[str]:
    return runner(
        args,
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )


def _locate_executable(executable: str) -> str:
    located = shutil.which(executable)
    if located is None:
        raise BoundaryError(
            f"SpecDD CLI executable was not found: {executable}"
        )
    return located


def _package_version(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None

    version = value.get("version") if isinstance(value, Mapping) else None
    return version if isinstance(version, str) and version else None


def specdd_cli_version(
    root: Path,
    executable: str,
    runner: RunCommand = subprocess.run,
) -> str:
    if runner is not subprocess.run:
        result = _run([executable, "--version"], root, runner)
        match = re.search(
            r"\b\d+\.\d+(?:\.\d+)?\b",
            result.stdout + "\n" + result.stderr,
        )
        if result.returncode == 0 and match:
            return match.group(0)
        raise BoundaryError(
            "Could not determine SpecDD CLI version from the supplied command runner"
        )

    executable_path = Path(_locate_executable(executable))
    candidates = [
        executable_path.parent
        / "node_modules"
        / "specdd"
        / "package.json",
        executable_path.parent.parent
        / "lib"
        / "node_modules"
        / "specdd"
        / "package.json",
    ]

    try:
        candidates.insert(
            0,
            executable_path.resolve().parent.parent / "package.json",
        )
    except OSError:
        pass

    for package_json in candidates:
        version = _package_version(package_json)
        if version:
            return version

    npm = shutil.which("npm")
    if npm:
        result = _run(
            [
                npm,
                "list",
                "--global",
                "specdd",
                "--depth=0",
                "--json",
            ],
            root,
            runner,
        )
        if result.returncode == 0:
            try:
                payload = json.loads(result.stdout)
                version = payload["dependencies"]["specdd"]["version"]
            except (json.JSONDecodeError, KeyError, TypeError):
                version = None

            if isinstance(version, str) and version:
                return version

    raise BoundaryError(
        "Could not determine the installed SpecDD CLI version"
    )


def framework_version(root: Path) -> str:
    for candidate in (root, *root.parents):
        bootstrap = candidate / ".specdd" / "bootstrap.md"
        if not bootstrap.is_file():
            continue

        for line in bootstrap.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^Version:\s*(\S+)\s*$", line)
            if match:
                return match.group(1)

    raise BoundaryError(
        f"Could not determine the SpecDD framework version from {root}"
    )


def resolve_target(
    root: Path,
    target: Target,
    executable: str,
    runner: RunCommand = subprocess.run,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    command = (
        executable
        if runner is not subprocess.run
        else _locate_executable(executable)
    )

    try:
        result = _run(
            [
                command,
                "resolve",
                "--root",
                str(root),
                str(target.absolute_path),
                "--sections",
                "all",
                "--format",
                "json",
            ],
            root,
            runner,
        )
    except FileNotFoundError as exc:
        raise BoundaryError(
            f"SpecDD CLI executable was not found: {executable}"
        ) from exc

    if result.returncode != 0:
        detail = " ".join(
            (result.stderr or result.stdout or "").split()
        )
        reason = (
            f"SpecDD resolve exited with status {result.returncode}"
        )
        return (
            None,
            f"{reason}: {detail}" if detail else reason,
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return (
            None,
            "SpecDD resolve returned malformed JSON: "
            f"{exc.msg} at line {exc.lineno} column {exc.colno}",
        )

    try:
        specs = extract_resolved_specs(payload, root)
    except BoundaryError as exc:
        return None, str(exc)

    if not specs:
        return (
            None,
            "SpecDD resolve returned no governing specifications",
        )

    return specs, None


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
            metadata_rule = _resolve_ref(schema, rule["$ref"])

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
            if isinstance(metadata_rule.get("required"), list)
            else set()
        )

        if required.issubset(values) and values:
            return str(name), values

    return None


def _resolved_schema_rule(
    schema: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> Mapping[str, Any]:
    if isinstance(rule.get("$ref"), str):
        return _resolve_ref(schema, rule["$ref"])
    return rule


def _unresolved_record(
    item: Unresolved,
    schema: Mapping[str, Any],
) -> dict[str, str]:
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

    item_rule = _resolved_schema_rule(schema, item_rule)
    item_properties = item_rule.get("properties")
    if not isinstance(item_properties, Mapping):
        raise BoundaryError(
            "Change Boundary schema does not define unresolved item properties"
        )

    names = [str(name) for name in item_properties]

    input_name = next(
        (
            name
            for name in names
            if name.lower() == "input"
        ),
        None,
    )
    if input_name is None:
        input_name = next(
            (
                name
                for name in names
                if any(
                    token in name.lower()
                    for token in (
                        "input",
                        "original",
                        "target",
                    )
                )
            ),
            None,
        )

    reason_name = next(
        (
            name
            for name in names
            if name.lower() == "reason"
        ),
        None,
    )
    if reason_name is None:
        reason_name = next(
            (
                name
                for name in names
                if any(
                    token in name.lower()
                    for token in (
                        "reason",
                        "error",
                        "diagnostic",
                        "message",
                        "detail",
                    )
                )
            ),
            None,
        )

    path_name = next(
        (
            name
            for name in names
            if name.lower() == "path"
        ),
        None,
    )
    if path_name is None:
        path_name = next(
            (
                name
                for name in names
                if (
                    "path" in name.lower()
                    or "normalized" in name.lower()
                )
            ),
            None,
        )

    if input_name is None or reason_name is None:
        raise BoundaryError(
            "Change Boundary schema has unrecognized unresolved-entry fields"
        )

    result = {
        input_name: item.input,
        reason_name: item.reason,
    }

    if item.path is not None and path_name is not None:
        result[path_name] = item.path

    return result


def build_change_boundary(
    root: Path,
    raw_targets: Iterable[str],
    *,
    feature: str,
    schema: Mapping[str, Any],
    executable: str = "specdd",
    runner: RunCommand = subprocess.run,
    cli_version: str | None = None,
    specdd_framework_version: str | None = None,
) -> dict[str, Any]:
    if not feature.strip():
        raise BoundaryError(
            "Feature identifier must not be empty"
        )

    normalized: dict[str, Target] = {}
    unresolved: list[Unresolved] = []
    had_input = False

    for raw in raw_targets:
        had_input = True

        try:
            target = normalize_target(root, raw)
        except BoundaryError as exc:
            unresolved.append(
                Unresolved(
                    input=raw or "<empty>",
                    reason=str(exc),
                )
            )
            continue

        if not target.absolute_path.exists():
            unresolved.append(
                Unresolved(
                    input=raw,
                    path=target.path,
                    reason=(
                        "Target does not exist; SpecDD resolve "
                        "requires existing targets"
                    ),
                )
            )
            continue

        normalized.setdefault(target.path, target)

    if not had_input:
        raise BoundaryError(
            "At least one target path is required"
        )

    cli_version = (
        cli_version
        or specdd_cli_version(root, executable, runner)
    )
    specdd_framework_version = (
        specdd_framework_version
        or framework_version(root)
    )

    targets: list[dict[str, Any]] = []
    authorities: set[str] = set()

    for path in sorted(normalized):
        target = normalized[path]
        specs, error = resolve_target(
            root,
            target,
            executable,
            runner,
        )

        if error or specs is None:
            unresolved.append(
                Unresolved(
                    input=target.raw,
                    path=target.path,
                    reason=error or "Unknown resolver error",
                )
            )
            continue

        authority, owners = derive_primary_authority(
            root,
            target.path,
            specs,
        )

        if authority is None:
            reason = (
                "No primary authority could be derived from resolved Owns entries"
                if not owners
                else (
                    "Multiple SpecDD specs claim ownership: "
                    + ", ".join(owners)
                )
            )
            unresolved.append(
                Unresolved(
                    input=target.raw,
                    path=target.path,
                    reason=reason,
                )
            )
            continue

        authorities.add(authority)
        targets.append(
            {
                "path": target.path,
                "primaryAuthority": authority,
                "resolvedSpecs": [
                    str(resolved_spec["path"])
                    for resolved_spec in specs
                ],
            }
        )

    unresolved_records = [
        _unresolved_record(item, schema)
        for item in unresolved
    ]
    unresolved_records.sort(
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "feature": feature.strip(),
        "targets": targets,
        "authorities": sorted(authorities),
        "crossBoundary": len(authorities) > 1,
        "unresolved": unresolved_records,
    }

    generation = _generation_metadata(
        schema,
        cli_version,
        specdd_framework_version,
    )
    if generation is not None:
        result[generation[0]] = generation[1]

    validate_boundary(result, schema)
    return result


def serialize_boundary(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def write_boundary(
    value: Mapping[str, Any],
    output: str | os.PathLike[str] | None,
) -> None:
    rendered = serialize_boundary(value)

    if output is None or str(output) == "-":
        sys.stdout.write(rendered)
        return

    output_path = Path(output).expanduser()
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=output_path.parent,
        prefix=output_path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)

    try:
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve existing targets into a Change Boundary v1 document."
        )
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Repository-relative or absolute target paths",
    )
    parser.add_argument(
        "--root",
        help=(
            "Resolution root; defaults to the discovered repository root"
        ),
    )
    parser.add_argument(
        "--feature",
        help=(
            "Feature identifier; defaults to the root directory name"
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Output path, or '-' for stdout (default)",
    )
    parser.add_argument(
        "--schema",
        help="Override the Change Boundary schema path",
    )
    parser.add_argument(
        "--specdd",
        default="specdd",
        help="SpecDD CLI executable (default: specdd)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        root = resolve_root(args.root)
        schema = load_schema(root, args.schema)
        value = build_change_boundary(
            root,
            args.targets,
            feature=args.feature or root.name,
            schema=schema,
            executable=args.specdd,
        )
        write_boundary(value, args.output)
    except BoundaryError as exc:
        print(
            f"boundary.py: {exc}",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
