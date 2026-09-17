from __future__ import annotations

import re
from pathlib import Path

from boundary_paths import normalize_target
from boundary_types import BoundaryError
from validation_types import TaskRecord

_TASK_RE = re.compile(
    r"^\s*-\s+\[(?: |x|X|-|!|\?)\]\s+(?P<body>.+?)\s*$"
)
_TASK_ID_RE = re.compile(
    r"^(?P<id>T\d+)\b"
)
_STORY_RE = re.compile(
    r"\[(?P<story>US\d+)\]"
)
_INLINE_CODE_RE = re.compile(
    r"`([^`\r\n]+)`"
)
_SLASH_PATH_RE = re.compile(
    r"(?P<path>"
    r"(?:\.{1,2}[\\/]|[\\/])?"
    r"[A-Za-z0-9_.-]+"
    r"(?:[\\/][A-Za-z0-9_.@+{}\[\]*?-]+)+"
    r"[\\/]?"
    r")"
)

_ROOT_FILE_SUFFIXES = {
    ".js",
    ".json",
    ".jsx",
    ".lock",
    ".md",
    ".ps1",
    ".py",
    ".sdd",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


def _clean_token(value: str) -> str:
    return value.strip().strip(
        "\"'()[]{}<>,;:"
    ).rstrip(".")


def _raw_targets(text: str) -> list[str]:
    values: list[str] = []

    for match in _SLASH_PATH_RE.finditer(text):
        prefix = text[
            max(0, match.start() - 12) : match.start()
        ]
        if "://" in prefix:
            continue

        value = _clean_token(
            match.group("path")
        )
        if value:
            values.append(value)

    for value in _INLINE_CODE_RE.findall(text):
        token = _clean_token(value)
        if not token:
            continue
        if "/" in token or "\\" in token:
            continue
        if Path(token).suffix.lower() in _ROOT_FILE_SUFFIXES:
            values.append(token)

    return list(dict.fromkeys(values))


def _normalize_task_target(
    root: Path,
    raw: str,
) -> str:
    candidate = raw.replace(
        "\\",
        "/",
    )

    if candidate.startswith("/") and not candidate.startswith("//"):
        candidate = candidate[1:]

    if any(
        character in candidate
        for character in "*?[]{}"
    ):
        raise BoundaryError(
            f"Task target must be an exact path: {raw}"
        )

    return normalize_target(
        root,
        candidate,
    ).path


def parse_tasks(
    root: Path,
    text: str,
) -> list[TaskRecord]:
    tasks: list[TaskRecord] = []

    for line in text.splitlines():
        match = _TASK_RE.match(line)
        if match is None:
            continue

        body = match.group("body")
        task_id_match = _TASK_ID_RE.match(body)
        story_match = _STORY_RE.search(body)

        targets: list[str] = []
        spec_targets: list[str] = []
        invalid_targets: list[str] = []

        for raw in _raw_targets(body):
            try:
                normalized = _normalize_task_target(
                    root,
                    raw,
                )
            except BoundaryError:
                invalid_targets.append(raw)
                continue

            collection = (
                spec_targets
                if normalized.lower().endswith(".sdd")
                else targets
            )
            if normalized not in collection:
                collection.append(normalized)

        tasks.append(
            TaskRecord(
                order=len(tasks),
                task_id=(
                    task_id_match.group("id")
                    if task_id_match
                    else None
                ),
                story=(
                    story_match.group("story")
                    if story_match
                    else None
                ),
                text=body,
                targets=tuple(targets),
                spec_targets=tuple(spec_targets),
                invalid_targets=tuple(
                    dict.fromkeys(
                        invalid_targets
                    )
                ),
            )
        )

    return tasks


def parse_tasks_file(
    root: Path,
    path: Path,
) -> list[TaskRecord]:
    return parse_tasks(
        root,
        path.read_text(
            encoding="utf-8"
        ),
    )
