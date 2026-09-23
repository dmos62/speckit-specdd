"""Git baseline and exact path-state capture for native authorization."""

from collections.abc import Sequence
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
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
        head=capture_git_head(root),
        dirty_path_states=capture_dirty_path_states(root),
    )


def capture_git_head(
    repository_root: str | Path,
) -> str | None:
    """Return current HEAD, including the unborn-repository case."""

    root = Path(repository_root)
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
        "could not determine Git HEAD"
        + (f": {detail}" if detail else "")
    )


def capture_dirty_path_states(
    repository_root: str | Path,
) -> tuple[DirtyPathState, ...]:
    """Return exact current states for every dirty Git path."""

    root = Path(repository_root)
    return tuple(
        DirtyPathState(
            path=path,
            state=path_state(root, path),
        )
        for path in _dirty_paths(root)
    )


def path_state(
    repository_root: str | Path,
    path: str,
) -> str:
    """Identify one path's combined Git index and worktree state."""

    root = Path(repository_root)
    canonical = normalize_repo_path(path)
    payload = {
        "schema": "boundary.git-path-state/v1",
        "index": _index_state(root, canonical),
        "worktree": _worktree_state(root, canonical),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


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
            "could not determine dirty Git paths"
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


def _index_state(root: Path, path: str) -> tuple[str, ...]:
    result = _run_git(
        root,
        ["ls-files", "--stage", "-z", "--", path],
    )
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise AuthorizationError(
            f"could not identify Git index state for {path}"
            + (f": {detail}" if detail else "")
        )
    return tuple(
        sorted(
            record
            for record in result.stdout.split("\0")
            if record
        )
    )


def _worktree_state(root: Path, path: str) -> dict[str, str]:
    absolute = root.joinpath(*PurePosixPath(path).parts)
    if not os.path.lexists(absolute):
        return {"kind": "missing"}

    try:
        metadata = absolute.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            payload = os.readlink(absolute).encode(
                "utf-8",
                errors="surrogateescape",
            )
            return {
                "kind": "symlink",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        if stat.S_ISREG(metadata.st_mode):
            payload = absolute.read_bytes()
            executable = bool(metadata.st_mode & 0o111)
            return {
                "kind": "file",
                "mode": "100755" if executable else "100644",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
    except OSError as exc:
        raise AuthorizationError(
            f"could not identify dirty Git path: {path}: {exc}"
        ) from exc

    raise AuthorizationError(
        f"dirty Git path is not a file or symlink: {path}"
    )


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
