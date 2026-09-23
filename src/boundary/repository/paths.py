"""Canonical repository-relative path handling."""

from pathlib import PurePosixPath


class RepositoryPathError(ValueError):
    """Raised when a path cannot be represented as a canonical repository path."""


def normalize_repo_path(value: str) -> str:
    """Return a canonical repository-relative POSIX path.

    The normalizer removes redundant ``.`` segments but rejects absolute paths,
    parent traversal, backslashes, NUL bytes, and empty paths. Filesystem state
    is intentionally not consulted.
    """

    if not isinstance(value, str):
        raise TypeError("repository path must be a string")
    if not value or "\x00" in value:
        raise RepositoryPathError("repository path must be non-empty")
    if "\\" in value:
        raise RepositoryPathError("repository path must use '/' separators")

    path = PurePosixPath(value)
    if path.is_absolute():
        raise RepositoryPathError("repository path must be relative")
    if ".." in path.parts:
        raise RepositoryPathError("repository path must not contain '..'")

    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise RepositoryPathError("repository path must identify a target")
    return normalized
