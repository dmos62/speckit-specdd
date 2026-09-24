#!/usr/bin/env python3
"""Concrete Spec Kit change-system projection for native Boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Callable

from boundary.authorization import (
    ChangeWriteSet,
    OperationRecord,
    TaskWriteSet,
    authorize_implementation_operation,
    read_current_operation,
)
from boundary.verification import finalize_operation_verification

_TASK_RE = re.compile(
    r"^\s*-\s+\[[ xX]\]\s+(?P<id>\S+)(?:\s+(?P<body>.*))?$"
)
_WRITES_RE = re.compile(r"^\s+Writes:\s*(?P<value>.*?)\s*$")
_WRITE_TOKEN_RE = re.compile(r"^`([^`\r\n]+)`$")
_STORY_RE = re.compile(r"\[(US[^\]]+)\]")


class SpecKitAdapterError(ValueError):
    """Raised when Spec Kit state cannot form one normalized change projection."""


def resolve_repository_root(value: str | Path | None = None) -> Path:
    """Resolve the repository root explicitly or through Git."""

    if value is not None:
        return Path(value).resolve()

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = " ".join((result.stderr or result.stdout).split())
        raise SpecKitAdapterError(
            "could not determine repository root"
            + (f": {detail}" if detail else "")
        )
    return Path(result.stdout.strip()).resolve()


def active_feature(root: Path) -> tuple[Path, str]:
    """Resolve the active Spec Kit feature directory and repository path."""

    configured = os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if configured:
        return _feature_path(root, configured)

    script = (
        root
        / ".specify"
        / "scripts"
        / "powershell"
        / "check-prerequisites.ps1"
    )
    if not script.is_file():
        raise SpecKitAdapterError(
            "Spec Kit prerequisite discovery is unavailable"
        )

    try:
        result = subprocess.run(
            ["pwsh", str(script), "-Json", "-PathsOnly"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SpecKitAdapterError(
            "required command not found: pwsh"
        ) from exc

    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout).split())
        raise SpecKitAdapterError(
            "Spec Kit could not resolve the active feature"
            + (f": {detail}" if detail else "")
        )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SpecKitAdapterError(
            "Spec Kit prerequisite discovery returned invalid JSON"
        ) from exc

    feature = value.get("FEATURE_DIR")
    if not isinstance(feature, str) or not feature:
        raise SpecKitAdapterError(
            "Spec Kit prerequisite discovery did not return FEATURE_DIR"
        )
    return _feature_path(root, feature)


def project_change(
    root: Path,
    feature_dir: Path,
) -> ChangeWriteSet:
    """Project one active feature into Boundary's normalized change model."""

    task_path = feature_dir / "tasks.md"
    try:
        source = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecKitAdapterError(
            f"active Spec Kit task file is unavailable: {task_path}: {exc}"
        ) from exc

    return ChangeWriteSet(
        change_id=feature_dir.name,
        tasks=parse_tasks(source),
    )


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


def authorize_feature(
    root: Path,
    feature_dir: Path,
) -> OperationRecord:
    """Fresh-authorize the active feature through native Boundary."""

    return authorize_implementation_operation(
        root,
        project_change(root, feature_dir),
    )


def verify_feature(
    root: Path,
    feature_dir: Path,
) -> OperationRecord:
    """Verify and close the active feature's Boundary operation."""

    current = read_current_operation(root)
    if current is None:
        raise SpecKitAdapterError(
            "no active Boundary operation is available for this feature"
        )
    if current.kind != "implementation":
        raise SpecKitAdapterError(
            "active Boundary operation is not an implementation operation"
        )
    if current.change_id != feature_dir.name:
        raise SpecKitAdapterError(
            "active Boundary operation belongs to another Spec Kit feature"
        )

    relative = feature_dir.relative_to(root).as_posix()
    return finalize_operation_verification(
        root,
        operation_id=current.operation_id,
        classify_path=path_classifier(relative),
    )


def path_classifier(
    feature_path: str,
) -> Callable[[str], str]:
    """Return deterministic Spec Kit bookkeeping classification."""

    feature_root = feature_path.rstrip("/")

    def classify(path: str) -> str:
        if path == ".specify" or path.startswith(".specify/"):
            return "change-system"
        if path == feature_root or path.startswith(f"{feature_root}/"):
            return "change-system"
        return "ordinary"

    return classify


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
    for part in text.split(","):
        token = part.strip()
        match = _WRITE_TOKEN_RE.fullmatch(token)
        if match is None:
            raise SpecKitAdapterError(
                f"task {task_id!r} Writes metadata must contain only "
                "comma-separated backticked paths"
            )
        writes.append(match.group(1))
    return tuple(writes)


def _feature_path(root: Path, configured: str) -> tuple[Path, str]:
    normalized = configured.replace("\\", "/")
    raw = PurePosixPath(normalized)
    candidate = Path(*raw.parts)
    if raw.is_absolute():
        candidate = Path(normalized)
    else:
        candidate = root / candidate

    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise SpecKitAdapterError(
            "active Spec Kit feature is outside the repository root"
        ) from exc
    if not resolved.is_dir():
        raise SpecKitAdapterError(
            f"active Spec Kit feature does not exist: {relative}"
        )
    return resolved, relative
