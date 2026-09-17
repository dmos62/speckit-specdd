from __future__ import annotations

import re
from pathlib import Path

from boundary_paths import normalize_target
from boundary_types import BoundaryError
from validation_types import (
    EVOLUTION_CLASSIFICATIONS, TaskRecord, diagnostic, task_fields,
)

_TASK_RE = re.compile(r"^\s*-\s+\[(?: |x|X|-|!|\?)\]\s+(?P<body>.+?)\s*$")
_TASK_ID_RE = re.compile(r"^(?P<id>T\d+)\b")
_STORY_RE = re.compile(r"\[(?P<story>US\d+)\]")
_INLINE_CODE_RE = re.compile(r"`([^`\r\n]+)`")
_URL_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s`]+")
_SLASH_PATH_RE = re.compile(
    r"(?P<path>(?:\.{1,2}[\\/]|[\\/])?[A-Za-z0-9_.-]+"
    r"(?:[\\/][A-Za-z0-9_.@+{}\[\]*?-]+)+[\\/]?)"
)
_EVOLUTION_RE = re.compile(
    r"\b(?:" + "|".join(EVOLUTION_CLASSIFICATIONS) + r")\b"
)
_ROOT_FILE_SUFFIXES = {
    ".js", ".json", ".jsx", ".lock", ".md", ".ps1", ".py", ".sdd",
    ".sh", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
_PATTERN_WILDCARDS = "*?"
_PATTERN_GROUPING = "[]{}"


def _clean_token(value: str) -> str:
    token = value.strip().strip("\"'()<>,;:").rstrip(".")
    if token.endswith("]") and "[" not in token[:-1]:
        token = token[:-1]
    if token.endswith("}") and "{" not in token[:-1]:
        token = token[:-1]
    return token


def _mask_ranges(text: str, ranges: list[tuple[int, int]]) -> str:
    masked = list(text)
    for start, end in ranges:
        masked[start:end] = " " * (end - start)
    return "".join(masked)


def _inline_path_candidate(value: str) -> bool:
    if not value or _URL_RE.fullmatch(value):
        return False
    return (
        "/" in value
        or "\\" in value
        or Path(value).suffix.lower() in _ROOT_FILE_SUFFIXES
    )


def _raw_targets(text: str) -> list[tuple[str, bool]]:
    candidates: list[tuple[int, str, bool]] = []
    inline_matches = list(_INLINE_CODE_RE.finditer(text))
    masked = _mask_ranges(
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


def _normalize_task_target(root: Path, raw: str, *, literal: bool) -> str:
    candidate = raw.replace("\\", "/")
    if candidate.startswith("/") and not candidate.startswith("//"):
        candidate = candidate[1:]
    if any(character in candidate for character in _PATTERN_WILDCARDS):
        raise BoundaryError(f"Task target must be an exact path: {raw}")
    if not literal and any(character in candidate for character in _PATTERN_GROUPING):
        raise BoundaryError(f"Task target must be an exact path: {raw}")
    return normalize_target(root, candidate).path


def extract_repository_targets(
    root: Path,
    text: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    targets: list[str] = []
    spec_targets: list[str] = []
    invalid_targets: list[str] = []
    for raw, literal in _raw_targets(text):
        try:
            normalized = _normalize_task_target(root, raw, literal=literal)
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


def parse_tasks(root: Path, text: str) -> list[TaskRecord]:
    tasks: list[TaskRecord] = []
    for line in text.splitlines():
        match = _TASK_RE.match(line)
        if match is None:
            continue
        body = match.group("body")
        task_id_match = _TASK_ID_RE.match(body)
        story_match = _STORY_RE.search(body)
        targets, spec_targets, invalid_targets = extract_repository_targets(root, body)
        tasks.append(TaskRecord(
            order=len(tasks),
            task_id=task_id_match.group("id") if task_id_match else None,
            story=story_match.group("story") if story_match else None,
            text=body,
            targets=targets,
            spec_targets=spec_targets,
            invalid_targets=invalid_targets,
            evolution_markers=tuple(dict.fromkeys(_EVOLUTION_RE.findall(body))),
        ))
    return tasks


def project_evolution(
    task: TaskRecord,
    *,
    severity: str,
) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    markers = list(dict.fromkeys(task.evolution_markers))
    if not markers:
        return None, []

    diagnostics: list[dict[str, object]] = []
    if len(markers) > 1:
        diagnostics.append(diagnostic(
            "EVOLUTION_CLASSIFICATION_CONFLICT",
            severity,
            "Task declares more than one SpecDD evolution class.",
            evolutionClassifications=markers,
            **task_fields(task),
        ))
        return {
            "classification": None,
            "markers": markers,
            "specTargets": list(task.spec_targets),
            "requiresFreshBoundary": True,
            "endsAuthorityContext": True,
        }, diagnostics

    classification = markers[0]
    if task.targets:
        diagnostics.append(diagnostic(
            "EVOLUTION_SCOPE_MIXED",
            severity,
            "SpecDD evolution must remain separate from ordinary implementation writes.",
            targets=list(task.targets),
            evolutionClassification=classification,
            **task_fields(task),
        ))
    if not task.spec_targets:
        diagnostics.append(diagnostic(
            "EVOLUTION_SPEC_TARGET_REQUIRED",
            severity,
            "SpecDD evolution must name at least one .sdd target.",
            evolutionClassification=classification,
            **task_fields(task),
        ))
    return {
        "classification": classification,
        "specTargets": list(task.spec_targets),
        "requiresFreshBoundary": True,
        "endsAuthorityContext": classification == "AUTHORITY_EVOLUTION_REQUIRED",
    }, diagnostics


def parse_tasks_file(root: Path, path: Path) -> list[TaskRecord]:
    return parse_tasks(root, path.read_text(encoding="utf-8"))
