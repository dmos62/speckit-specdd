from __future__ import annotations

import re
from pathlib import Path

from boundary_paths import normalize_target
from boundary_types import BoundaryError

_INLINE_CODE_RE = re.compile(r"`([^`\r\n]+)`")
_URL_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s`]+")
_SLASH_PATH_RE = re.compile(
    r"(?P<path>(?:\.{1,2}[\\/]|[\\/])?[A-Za-z0-9_.-]+"
    r"(?:[\\/][A-Za-z0-9_.@+{}\[\]*?-]+)+[\\/]?)"
)
_ROOT_FILE_SUFFIXES = {
    ".js", ".json", ".jsx", ".lock", ".md", ".ps1", ".py", ".sdd",
    ".sh", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
_PATTERN_WILDCARDS = "*?"
_PATTERN_GROUPING = "[]{}"


def is_specdd_control_path(path: str) -> bool:
    return path.startswith(".specdd/") and not path.lower().endswith(".sdd")


def mask_ranges(text: str, ranges: list[tuple[int, int]]) -> str:
    masked = list(text)
    for start, end in ranges:
        masked[start:end] = " " * (end - start)
    return "".join(masked)


def inline_code_matches(text: str) -> list[re.Match[str]]:
    return list(_INLINE_CODE_RE.finditer(text))


def normalize_task_target(root: Path, raw: str, *, literal: bool) -> str:
    candidate = raw.replace("\\", "/")
    if candidate.startswith("/") and not candidate.startswith("//"):
        candidate = candidate[1:]
    if any(character in candidate for character in _PATTERN_WILDCARDS):
        raise BoundaryError(f"Task target must be an exact path: {raw}")
    if not literal and any(
        character in candidate for character in _PATTERN_GROUPING
    ):
        raise BoundaryError(f"Task target must be an exact path: {raw}")
    return normalize_target(root, candidate).path


def extract_repository_targets(
    root: Path,
    text: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Heuristically discover paths for advisory planning only."""

    targets: list[str] = []
    spec_targets: list[str] = []
    invalid_targets: list[str] = []
    for raw, literal in _raw_advisory_targets(text):
        try:
            normalized = normalize_task_target(root, raw, literal=literal)
        except BoundaryError:
            invalid_targets.append(raw)
            continue
        collection = spec_targets if normalized.lower().endswith(".sdd") else targets
        if normalized not in collection:
            collection.append(normalized)
    return (
        tuple(targets),
        tuple(spec_targets),
        tuple(dict.fromkeys(invalid_targets)),
    )


def _raw_advisory_targets(text: str) -> list[tuple[str, bool]]:
    candidates: list[tuple[int, str, bool]] = []
    inline_matches = inline_code_matches(text)
    masked = mask_ranges(
        text,
        [
            *(match.span() for match in inline_matches),
            *(match.span() for match in _URL_RE.finditer(text)),
        ],
    )
    for match in _SLASH_PATH_RE.finditer(masked):
        value = _clean_token(match.group("path"))
        if value:
            candidates.append((match.start(), value, False))
    for match in inline_matches:
        value = _clean_token(match.group(1))
        if _inline_path_candidate(value):
            candidates.append((match.start(), value, True))
    candidates.sort(key=lambda item: item[0])
    values: dict[str, bool] = {}
    for _, value, literal in candidates:
        values[value] = values.get(value, False) or literal
    return list(values.items())


def _inline_path_candidate(value: str) -> bool:
    return bool(
        value
        and not _URL_RE.fullmatch(value)
        and (
            "/" in value
            or "\\" in value
            or Path(value).suffix.lower() in _ROOT_FILE_SUFFIXES
        )
    )


def _clean_token(value: str) -> str:
    token = value.strip().strip("\"'()<>,;:").rstrip(".")
    if token.endswith("]") and "[" not in token[:-1]:
        token = token[:-1]
    if token.endswith("}") and "{" not in token[:-1]:
        token = token[:-1]
    return token
