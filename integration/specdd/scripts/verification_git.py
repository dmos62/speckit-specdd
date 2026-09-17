from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from boundary_paths import normalize_target
from boundary_types import BoundaryError
from verification_types import (
    ChangeSet,
    GitChange,
    VerificationError,
)

RunGit = Callable[..., subprocess.CompletedProcess[str]]

_GENERATED_PREFIXES = (
    ".specify/",
    ".specify-agent/",
)
_GENERATED_EXACT = {
    ".specdd/bootstrap.local.md",
}


def _run_git(
    root: Path,
    runner: RunGit,
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            [
                "git",
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--no-renames",
            ],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise VerificationError(
            "Git executable was not found"
        ) from exc


def _status_name(value: str) -> str:
    if value == "??":
        return "UNTRACKED"
    if "D" in value:
        return "DELETED"
    if "A" in value:
        return "ADDED"
    if "M" in value:
        return "MODIFIED"
    return "CHANGED"


def _inside(
    path: str,
    directory: str | None,
) -> bool:
    if directory is None:
        return False
    return (
        path == directory
        or path.startswith(directory.rstrip("/") + "/")
    )


def _feature_path(
    root: Path,
    feature_dir: str | Path | None,
) -> str | None:
    if feature_dir is None:
        return None

    try:
        return normalize_target(
            root,
            str(feature_dir),
        ).path
    except BoundaryError as exc:
        raise VerificationError(
            f"Active feature directory is invalid: {feature_dir}: {exc}"
        ) from exc


def _category(
    path: str,
    feature_dir: str | None,
) -> str:
    if _inside(path, feature_dir):
        return "feature"

    if (
        path in _GENERATED_EXACT
        or any(
            path.startswith(prefix)
            for prefix in _GENERATED_PREFIXES
        )
    ):
        return "generated"

    if path.startswith(".specdd/"):
        return "control"

    if path.lower().endswith(".sdd"):
        return "spec"

    return "write"


def collect_git_changes(
    root: Path,
    *,
    feature_dir: str | Path | None = None,
    runner: RunGit = subprocess.run,
) -> ChangeSet:
    result = _run_git(
        root,
        runner,
    )
    if result.returncode != 0:
        detail = " ".join(
            (
                result.stderr
                or result.stdout
                or ""
            ).split()
        )
        raise VerificationError(
            "Could not determine changed paths from Git"
            + (f": {detail}" if detail else "")
        )

    feature_path = _feature_path(
        root,
        feature_dir,
    )
    groups: dict[str, list[GitChange]] = {
        "write": [],
        "spec": [],
        "control": [],
        "feature": [],
        "generated": [],
    }

    for record in result.stdout.split("\0"):
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise VerificationError(
                "Git returned an unexpected porcelain status record"
            )

        raw_path = record[3:]
        try:
            target = normalize_target(
                root,
                raw_path,
            )
        except BoundaryError as exc:
            raise VerificationError(
                f"Git returned an invalid repository path: {raw_path}: {exc}"
            ) from exc

        groups[_category(
            target.path,
            feature_path,
        )].append(
            GitChange(
                path=target.path,
                status=_status_name(record[:2]),
                deleted=not target.absolute_path.exists(),
            )
        )

    for values in groups.values():
        values.sort(
            key=lambda item: item.path
        )

    return ChangeSet(
        writes=tuple(groups["write"]),
        specs=tuple(groups["spec"]),
        controls=tuple(groups["control"]),
        feature_artifacts=tuple(groups["feature"]),
        generated=tuple(groups["generated"]),
    )
