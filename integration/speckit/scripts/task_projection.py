"""Structured Spec Kit task projection for native Boundary authorization."""

from __future__ import annotations

import re

from boundary.authorization import TaskWriteSet

from spec_kit_errors import SpecKitAdapterError

_TASK_RE = re.compile(
    r"^\s*-\s+\[[ xX]\]\s+(?P<id>\S+)(?:\s+(?P<body>.*))?$"
)
_WRITES_RE = re.compile(r"^\s+Writes:\s*(?P<value>.*?)\s*$")
_STORY_RE = re.compile(r"\[(US[^\]]+)\]")


def parse_tasks(source: str) -> tuple[TaskWriteSet, ...]:
    """Parse checklist task identity and directly attached Writes metadata."""

    tasks: list[TaskWriteSet] = []
    current_id: str | None = None
    current_story: str | None = None
    current_writes: tuple[str, ...] = ()
    writes_seen = False
    metadata_open = False

    def flush() -> None:
        nonlocal current_id, current_story, current_writes
        nonlocal writes_seen, metadata_open
        if current_id is None:
            return
        tasks.append(
            TaskWriteSet(
                order=len(tasks),
                task_id=current_id,
                story=current_story,
                writes=current_writes,
            )
        )
        current_id = None
        current_story = None
        current_writes = ()
        writes_seen = False
        metadata_open = False

    for line in source.splitlines():
        task_match = _TASK_RE.match(line)
        if task_match is not None:
            flush()
            current_id = task_match.group("id")
            body = task_match.group("body") or ""
            story_match = _STORY_RE.search(body)
            current_story = (
                story_match.group(1)
                if story_match is not None
                else None
            )
            metadata_open = True
            continue

        writes_match = _WRITES_RE.match(line)
        if writes_match is not None:
            if current_id is None:
                raise SpecKitAdapterError(
                    "Writes metadata must belong to a checklist task"
                )
            if not metadata_open:
                raise SpecKitAdapterError(
                    f"task {current_id!r} Writes metadata must be directly "
                    "attached to the checklist task"
                )
            if writes_seen:
                raise SpecKitAdapterError(
                    f"task {current_id!r} contains duplicate Writes metadata"
                )
            writes_seen = True
            current_writes = _parse_writes(
                current_id,
                writes_match.group("value"),
            )
            continue

        if current_id is not None and line.strip():
            metadata_open = False

    flush()
    if not tasks:
        raise SpecKitAdapterError(
            "active Spec Kit task file contains no checklist tasks"
        )
    return tuple(tasks)


def _parse_writes(
    task_id: str,
    value: str,
) -> tuple[str, ...]:
    text = value.strip()
    if not text:
        raise SpecKitAdapterError(
            f"task {task_id!r} Writes metadata must declare at least one path"
        )

    writes: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "`":
            raise _writes_syntax_error(task_id)

        end = text.find("`", index + 1)
        if end < 0 or end == index + 1:
            raise _writes_syntax_error(task_id)
        writes.append(text[index + 1 : end])
        index = end + 1

        if index == len(text):
            break

        if text[index] == ",":
            index += 1
            while index < len(text) and text[index].isspace():
                index += 1
        elif text[index].isspace():
            while index < len(text) and text[index].isspace():
                index += 1
        else:
            raise _writes_syntax_error(task_id)

        if index >= len(text):
            raise _writes_syntax_error(task_id)

    return tuple(writes)


def _writes_syntax_error(task_id: str) -> SpecKitAdapterError:
    return SpecKitAdapterError(
        f"task {task_id!r} Writes metadata must contain only "
        "comma-separated backticked paths or backticked paths "
        "separated by whitespace"
    )
