from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from boundary_types import BoundaryError, Target


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
        if (candidate / ".git").exists() or (
            candidate / ".specdd" / "bootstrap.md"
        ).is_file():
            return candidate

    raise BoundaryError(f"Could not discover a repository root from {start_path}")


def resolve_root(explicit_root: str | os.PathLike[str] | None) -> Path:
    root = (
        Path(explicit_root).expanduser().resolve()
        if explicit_root
        else discover_repository_root()
    )
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
        raise BoundaryError(
            f"Target uses an absolute Windows path on this host: {raw}"
        )

    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root.joinpath(
            *PurePosixPath(value.replace("\\", "/")).parts
        )

    absolute = candidate.resolve(strict=False)
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise BoundaryError(
            f"Target is outside repository root: {raw}"
        ) from exc

    normalized = relative.as_posix()
    if normalized in {"", "."}:
        raise BoundaryError(
            f"Target must identify a path inside the repository: {raw}"
        )

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
            raise BoundaryError(
                f"SpecDD resolver returned a path outside the root: {raw}"
            ) from exc
    else:
        value = value.replace("\\", "/")
        if value.startswith("./"):
            value = value[2:]
        parts = PurePosixPath(value).parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise BoundaryError(
                f"SpecDD resolver returned a non-normalized path: {raw}"
            )
        value = PurePosixPath(*parts).as_posix()

    if value.startswith("/") or value.endswith("/") or "//" in value:
        raise BoundaryError(
            f"SpecDD resolver returned an invalid repository path: {raw}"
        )
    if spec and not value.lower().endswith(".sdd"):
        raise BoundaryError(
            f"Resolved spec path does not end in .sdd: {raw}"
        )

    return value


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
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
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
                    pieces.append("[^" + re.escape(content[1:]) + "]")
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


def _ownership_matches(root: Path, pattern: str, target: str) -> bool:
    if any(character in pattern for character in "*?[]{}"):
        return _glob_matches(pattern, target)

    if pattern == target:
        return True

    path = root.joinpath(*PurePosixPath(pattern).parts)
    return path.is_dir() and target.startswith(pattern.rstrip("/") + "/")
