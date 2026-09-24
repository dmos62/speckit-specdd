#!/usr/bin/env python3
"""Concrete Spec Kit change-system projection for native Boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Callable

from boundary.authorization import (
    ChangeWriteSet,
    OperationRecord,
    authorize_implementation_operation,
    read_current_operation,
)
from boundary.verification import finalize_operation_verification

from spec_kit_errors import SpecKitAdapterError
from task_projection import parse_tasks


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
