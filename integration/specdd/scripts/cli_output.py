from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

FAIL_ON = ("never", "error", "blocking")


def root_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def serialize_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"


def write_json_output(
    root: Path,
    value: Mapping[str, Any],
    output: str,
) -> None:
    rendered = serialize_json(value)
    if output == "-":
        sys.stdout.write(rendered)
        return

    output_path = root_path(root, output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=output_path.parent,
        prefix=output_path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)

    try:
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)


def result_exit_code(
    result: Mapping[str, Any],
    fail_on: str,
) -> int:
    if fail_on == "never":
        return 0

    summary = result.get("summary", {})
    counts = (
        summary.get("countsBySeverity", {})
        if isinstance(summary, Mapping)
        else {}
    )
    if not isinstance(counts, Mapping):
        return 0
    if fail_on == "blocking":
        return 1 if counts.get("blocking", 0) else 0
    return (
        1
        if counts.get("error", 0)
        or counts.get("blocking", 0)
        else 0
    )
