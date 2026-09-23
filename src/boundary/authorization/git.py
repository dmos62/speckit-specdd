"""Git baseline capture for native operation authorization."""

from collections.abc import Sequence
import hashlib
import os
from pathlib import Path, PurePosixPath
import subprocess

from boundary.repository import RepositoryPathError, normalize_repo_path

from .model import AuthorizationError
from .record import DirtyPathState, GitBaseline


def capture_git_baseline(
    repository_root: str | Path,
) -> GitBaseline:
    """Capture authorization-time HEAD and exact dirty-path identities."""

    root = Path(repository_root)
    return GitBaseline(
        head=_git_head(root),
        dirty_path_states=tuple(
            DirtyPathState(
                path=path,
                state=_path_state(root, path),
            )
            for path in _dirty_paths(root)
        ),
    )


def git_metadata_directory(
    repository_root: str | Path,
) -> Path:
    """Return current-worktree Git metadata without assuming `.git/`."""

    root = Path(repository_root)
    result = _run_git(root, ["rev-parse", "--git-dir"])
    if result.returncode != 0 or not result.stdout.strip():
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise AuthorizationError(
            "could not determine the Git metadata directory"
            + (f": {detail}" if detail else "")
        )
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=False)


def _git_head(root: Path) -> str | None:
    result = _run_git(
        root,
        ["rev-parse", "--verify", "--quiet", "HEAD"],
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    if result.returncode == 1 and not (result.stderr or result.stdout).strip():
        return None
    detail = " ".join((result.stderr or result.stdout or "").split())
    raise AuthorizationError(
        "could not determine authorization-time Git HEAD"
        + (f": {detail}" if detail else "")
    )


def _dirty_paths(root: Path) -> tuple[str, ...]:
    result = _run_git(
        root,
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--no-renames",
        ],
    )
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise AuthorizationError(
            "could not determine authorization-time dirty paths"
            + (f": {detail}" if detail else "")
        )

    paths: set[str] = set()
    for record in result.stdout.split("\0"):
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise AuthorizationError(
                "Git returned an unexpected porcelain status record"
            )
        raw = record[3:]
        try:
            paths.add(normalize_repo_path(raw))
        except RepositoryPathError as exc:
            raise AuthorizationError(
                f"Git returned an invalid repository path: {raw}"
            ) from exc
    return tuple(sorted(paths))


def _path_state(root: Path, path: str) -> str:
    absolute = root.joinpath(*PurePosixPath(path).parts)
    if not os.path.lexists(absolute):
        return "deleted"
    try:
        if absolute.is_symlink():
            payload = os.readlink(absolute).encode(
                "utf-8",
                errors="surrogateescape",
            )
            kind = "symlink"
        elif absolute.is_file():
            payload = absolute.read_bytes()
            kind = "file"
        else:
            raise AuthorizationError(
                f"dirty Git path is not a file or symlink: {path}"
            )
    except OSError as exc:
        raise AuthorizationError(
            f"could not identify dirty Git path: {path}: {exc}"
        ) from exc
    return f"{kind}:sha256:{hashlib.sha256(payload).hexdigest()}"


def _run_git(
    root: Path,
    args: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise AuthorizationError(
            "required Git executable was not found"
        ) from exc
    except OSError as exc:
        raise AuthorizationError(f"Git could not be executed: {exc}") from exc
