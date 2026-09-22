from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

from boundary_types import BoundaryError, RunCommand

PINNED_SPECDD_CLI_VERSION = "1.2.0"
_INTENDED_TARGET_FLAGS = ("--file", "--folder", "--sdd-file")


def _run(
    args: Sequence[str],
    root: Path,
    runner: RunCommand,
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            args,
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        command = args[0] if args else "<unknown>"
        raise BoundaryError(
            f"External command could not be executed: {command}: {exc}"
        ) from exc


def normalize_command_output(root: Path, value: str) -> str:
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    resolved_root = root.resolve(strict=False)
    native_root = str(resolved_root).rstrip("\\/")
    posix_root = resolved_root.as_posix().rstrip("/")
    replacements = {
        native_root + "\\": "./",
        native_root + "/": "./",
        posix_root + "/": "./",
        native_root: ".",
        posix_root: ".",
    }
    for source in sorted(replacements, key=len, reverse=True):
        if source:
            text = text.replace(source, replacements[source])
    if os.name == "nt":
        text = text.replace("\\", "/")
    return text.strip()


def _locate_executable(executable: str) -> str:
    located = shutil.which(executable)
    if located is None:
        raise BoundaryError(
            "Required SpecDD CLI executable was not found: "
            f"{executable}. Run `bash scripts/bootstrap.sh` to install "
            "the pinned SpecDD CLI, or restore it to PATH before retrying."
        )
    return located


def specdd_resolve_supports_intended_targets(
    root: Path,
    executable: str,
    runner: RunCommand = subprocess.run,
) -> bool:
    command = (
        executable
        if runner is not subprocess.run
        else _locate_executable(executable)
    )
    result = _run([command, "resolve", "--help"], root, runner)
    if result.returncode != 0:
        output = result.stderr or result.stdout or ""
        detail = " ".join(normalize_command_output(root, output).split())
        raise BoundaryError(
            "Could not inspect SpecDD resolve capabilities"
            + (f": {detail}" if detail else "")
        )
    output = result.stdout + "\n" + result.stderr
    return all(flag in output for flag in _INTENDED_TARGET_FLAGS)


def validate_intended_target_capabilities(
    cli_version: str,
    supported: bool,
) -> None:
    if supported or cli_version != PINNED_SPECDD_CLI_VERSION:
        return

    flags = ", ".join(_INTENDED_TARGET_FLAGS)
    raise BoundaryError(
        f"SpecDD CLI {PINNED_SPECDD_CLI_VERSION} is installed but its "
        "resolver does not expose the complete typed intended-target flag "
        f"set ({flags}). The pinned SpecDD CLI installation is invalid; "
        "run `bash scripts/bootstrap.sh` to repair it."
    )


def _package_version(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None

    version = value.get("version") if isinstance(value, Mapping) else None
    return version if isinstance(version, str) and version else None


def specdd_cli_version(
    root: Path,
    executable: str,
    runner: RunCommand = subprocess.run,
) -> str:
    if runner is not subprocess.run:
        result = _run([executable, "--version"], root, runner)
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

    executable_path = Path(_locate_executable(executable))
    candidates = [
        executable_path.parent / "node_modules" / "specdd" / "package.json",
        executable_path.parent.parent
        / "lib"
        / "node_modules"
        / "specdd"
        / "package.json",
    ]
    try:
        candidates.insert(
            0,
            executable_path.resolve().parent.parent / "package.json",
        )
    except OSError:
        pass

    for package_json in candidates:
        version = _package_version(package_json)
        if version:
            return version

    npm = shutil.which("npm")
    if npm is None:
        raise BoundaryError(
            "SpecDD CLI is present, but its installed version could not "
            "be verified because npm was not found. Install Node.js/npm "
            "and run `bash scripts/bootstrap.sh --check`."
        )

    result = _run(
        [npm, "list", "--global", "specdd", "--depth=0", "--json"],
        root,
        runner,
    )
    if result.returncode == 0:
        try:
            payload = json.loads(result.stdout)
            version = payload["dependencies"]["specdd"]["version"]
        except (json.JSONDecodeError, KeyError, TypeError):
            version = None
        if isinstance(version, str) and version:
            return version

    raise BoundaryError(
        "SpecDD CLI is present, but its installed version could not be "
        "verified from package metadata or npm global package state. "
        "Run `bash scripts/bootstrap.sh --check` to repair the pinned toolchain."
    )


def framework_version(root: Path) -> str:
    for candidate in (root, *root.parents):
        bootstrap = candidate / ".specdd" / "bootstrap.md"
        if not bootstrap.is_file():
            continue
        for line in bootstrap.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^Version:\s*(\S+)\s*$", line)
            if match:
                return match.group(1)

    raise BoundaryError(
        "Could not determine the SpecDD framework version "
        f"from {root}"
    )
