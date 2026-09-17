from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

from boundary_types import BoundaryError, RunCommand


def _run(
    args: Sequence[str],
    root: Path,
    runner: RunCommand,
) -> subprocess.CompletedProcess[str]:
    return runner(
        args,
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )


def _locate_executable(executable: str) -> str:
    located = shutil.which(executable)
    if located is None:
        raise BoundaryError(
            f"SpecDD CLI executable was not found: {executable}"
        )
    return located


def _package_version(path: Path) -> str | None:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (
        FileNotFoundError,
        OSError,
        json.JSONDecodeError,
    ):
        return None

    version = (
        value.get("version")
        if isinstance(value, Mapping)
        else None
    )
    return (
        version
        if isinstance(version, str) and version
        else None
    )


def specdd_cli_version(
    root: Path,
    executable: str,
    runner: RunCommand = subprocess.run,
) -> str:
    if runner is not subprocess.run:
        result = _run(
            [executable, "--version"],
            root,
            runner,
        )
        match = re.search(
            r"\b\d+\.\d+(?:\.\d+)?\b",
            result.stdout + "\n" + result.stderr,
        )
        if result.returncode == 0 and match:
            return match.group(0)

        raise BoundaryError(
            "Could not determine SpecDD CLI version from the supplied "
            "command runner"
        )

    executable_path = Path(
        _locate_executable(executable)
    )
    candidates = [
        executable_path.parent
        / "node_modules"
        / "specdd"
        / "package.json",
        executable_path.parent.parent
        / "lib"
        / "node_modules"
        / "specdd"
        / "package.json",
    ]

    try:
        candidates.insert(
            0,
            executable_path.resolve().parent.parent
            / "package.json",
        )
    except OSError:
        pass

    for package_json in candidates:
        version = _package_version(package_json)
        if version:
            return version

    npm = shutil.which("npm")
    if npm:
        result = _run(
            [
                npm,
                "list",
                "--global",
                "specdd",
                "--depth=0",
                "--json",
            ],
            root,
            runner,
        )
        if result.returncode == 0:
            try:
                payload = json.loads(result.stdout)
                version = payload["dependencies"]["specdd"][
                    "version"
                ]
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
            ):
                version = None

            if isinstance(version, str) and version:
                return version

    raise BoundaryError(
        "Could not determine the installed SpecDD CLI version"
    )


def framework_version(root: Path) -> str:
    for candidate in (root, *root.parents):
        bootstrap = (
            candidate / ".specdd" / "bootstrap.md"
        )
        if not bootstrap.is_file():
            continue

        for line in bootstrap.read_text(
            encoding="utf-8"
        ).splitlines():
            match = re.match(
                r"^Version:\s*(\S+)\s*$",
                line,
            )
            if match:
                return match.group(1)

    raise BoundaryError(
        "Could not determine the SpecDD framework version "
        f"from {root}"
    )
