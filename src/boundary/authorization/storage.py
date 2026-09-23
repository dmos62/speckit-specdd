"""Atomic current-operation persistence in current-worktree Git metadata."""

import json
import os
from pathlib import Path
import tempfile

from .git import git_metadata_directory
from .model import AuthorizationError
from .record import OperationRecord

_CURRENT_RELATIVE_PATH = Path("boundary") / "current.json"


def current_operation_path(
    repository_root: str | Path,
) -> Path:
    """Return the native active-operation evidence path."""

    return (
        git_metadata_directory(repository_root)
        / _CURRENT_RELATIVE_PATH
    )


def write_current_operation(
    repository_root: str | Path,
    record: OperationRecord,
) -> Path:
    """Atomically replace active evidence after the full record is ready."""

    output = current_operation_path(repository_root)
    rendered = json.dumps(
        record.to_document(),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"

    temporary: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
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
            temporary = Path(handle.name)
        os.replace(temporary, output)
        temporary = None
    except OSError as exc:
        raise AuthorizationError(
            f"could not store atomic operation evidence: {exc}"
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    return output
