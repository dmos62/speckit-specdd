"""Atomic operation persistence in current-worktree Git metadata."""

import json
import os
from pathlib import Path
import tempfile

from .codec import operation_record_from_document
from .git import git_metadata_directory
from .model import AuthorizationError
from .record import OperationRecord

_CURRENT_RELATIVE_PATH = Path("boundary") / "current.json"
_ARCHIVE_RELATIVE_ROOT = Path("boundary") / "operations"


def current_operation_path(
    repository_root: str | Path,
) -> Path:
    """Return the native active-operation evidence path."""

    return (
        git_metadata_directory(repository_root)
        / _CURRENT_RELATIVE_PATH
    )


def operation_archive_path(
    repository_root: str | Path,
    operation_id: str,
) -> Path:
    """Return the immutable archive path for one operation identifier."""

    if not operation_id or any(
        char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
        for char in operation_id
    ):
        raise AuthorizationError(
            "operation id contains unsupported characters"
        )
    return (
        git_metadata_directory(repository_root)
        / _ARCHIVE_RELATIVE_ROOT
        / f"{operation_id}.json"
    )


def read_current_operation(
    repository_root: str | Path,
) -> OperationRecord | None:
    """Load current operation evidence when present."""

    path = current_operation_path(repository_root)
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise AuthorizationError(
            f"could not read current operation evidence: {exc}"
        ) from exc

    try:
        value = json.loads(source)
    except json.JSONDecodeError as exc:
        raise AuthorizationError(
            f"current operation evidence is invalid JSON: {exc}"
        ) from exc
    return operation_record_from_document(value)


def write_current_operation(
    repository_root: str | Path,
    record: OperationRecord,
) -> Path:
    """Atomically replace active evidence after the full record is ready."""

    output = current_operation_path(repository_root)
    _write_replacing(output, _render_record(record))
    return output


def archive_operation(
    repository_root: str | Path,
    record: OperationRecord,
) -> Path:
    """Persist one verified predecessor as immutable historical evidence."""

    if record.status != "verified":
        raise AuthorizationError(
            "only verified operations may be archived"
        )
    output = operation_archive_path(
        repository_root,
        record.operation_id,
    )
    _write_immutable(output, _render_record(record))
    return output


def _render_record(record: OperationRecord) -> str:
    return (
        json.dumps(
            record.to_document(),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    )


def _write_replacing(output: Path, rendered: str) -> None:
    temporary: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = _write_temporary(output, rendered)
        os.replace(temporary, output)
        temporary = None
    except OSError as exc:
        raise AuthorizationError(
            f"could not store atomic operation evidence: {exc}"
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_immutable(output: Path, rendered: str) -> None:
    temporary: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            _require_same_archive(output, rendered)
            return

        temporary = _write_temporary(output, rendered)
        try:
            os.link(temporary, output)
        except FileExistsError:
            _require_same_archive(output, rendered)
        temporary.unlink(missing_ok=True)
        temporary = None
    except OSError as exc:
        raise AuthorizationError(
            f"could not archive immutable operation evidence: {exc}"
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_temporary(output: Path, rendered: str) -> Path:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=output.parent,
        prefix=output.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(rendered)
        return Path(handle.name)


def _require_same_archive(
    output: Path,
    rendered: str,
) -> None:
    try:
        existing = output.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuthorizationError(
            f"could not read archived operation evidence: {exc}"
        ) from exc
    if existing != rendered:
        raise AuthorizationError(
            "immutable operation archive already exists with "
            f"different evidence: {output.name}"
        )
