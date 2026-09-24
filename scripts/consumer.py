#!/usr/bin/env python3
"""Manage downstream Boundary state from one committed immutable lock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Sequence

from consumer_lock import (
    BoundaryLock,
    BoundaryLockError,
    load_lock,
    materialize_locked_source,
    write_lock,
)

_DEFAULT_LOCK = "boundary.lock.json"
_PROVENANCE = Path(".specify") / "boundary-runtime" / "source-lock.json"
_EXCLUDE_BEGIN = "# BEGIN Boundary generated state"
_EXCLUDE_END = "# END Boundary generated state"
_GENERATED_EXCLUDES = (
    "/.agents/skills/boundary-scope/",
    "/.agents/skills/boundary-implement/",
    "/.agents/skills/boundary-contracts/",
    "/.agents/skills/speckit-boundary-authorize/",
    "/.agents/skills/speckit-boundary-verify/",
    "/.specify/boundary-runtime/",
    "/.specify/extensions/boundary/",
    "/.specify/presets/boundary/",
    "/.specify/workflows/overlays/speckit/boundary.yml",
)


class ConsumerError(RuntimeError):
    """Raised when downstream reconstruction cannot complete safely."""


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconstruct downstream Boundary state from its lock."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Downstream repository root.",
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path(_DEFAULT_LOCK),
        help="Boundary lock path, relative to the downstream root by default.",
    )

    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("install")
    commands.add_parser("check")
    commands.add_parser("remove")
    commands.add_parser("reinstall")

    upgrade = commands.add_parser("upgrade")
    upgrade.add_argument("--source", required=True)
    upgrade.add_argument("--revision", required=True)
    upgrade.add_argument("--sha256", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    lock_path = args.lock
    if not lock_path.is_absolute():
        lock_path = root / lock_path

    try:
        if args.command == "upgrade":
            replacement = BoundaryLock(
                source_url=args.source,
                revision=args.revision,
                sha256=args.sha256,
            )
            _upgrade(root, lock_path, replacement)
        else:
            lock = load_lock(lock_path)
            if args.command == "install":
                _install(root, lock)
            elif args.command == "check":
                _check(root, lock)
            elif args.command == "remove":
                _remove(root, lock)
            elif args.command == "reinstall":
                _remove(root, lock)
                _install(root, lock)
    except (BoundaryLockError, ConsumerError, OSError) as exc:
        print(f"boundary consumer: {exc}", file=sys.stderr)
        return 2
    return 0


def _install(root: Path, lock: BoundaryLock) -> None:
    _with_source(root, lock, "install")
    _write_provenance(root, lock)
    _update_local_excludes(root, enabled=True)


def _check(root: Path, lock: BoundaryLock) -> None:
    _require_provenance(root, lock)
    _with_source(root, lock, "check")
    _require_local_excludes(root)


def _remove(root: Path, lock: BoundaryLock) -> None:
    _with_source(root, lock, "remove")
    _update_local_excludes(root, enabled=False)


def _upgrade(
    root: Path,
    lock_path: Path,
    replacement: BoundaryLock,
) -> None:
    previous = load_lock(lock_path)
    try:
        _install(root, replacement)
        write_lock(lock_path, replacement)
    except Exception as exc:
        try:
            _install(root, previous)
        except Exception as rollback_exc:
            raise ConsumerError(
                "upgrade failed and the previous locked installation could "
                f"not be restored: {rollback_exc}"
            ) from exc
        raise


def _with_source(
    root: Path,
    lock: BoundaryLock,
    action: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="boundary-consumer-") as temp:
        source_root = materialize_locked_source(lock, temp)
        command = ["bash", str(source_root / "scripts" / "install.sh")]
        if action == "install":
            command.extend(["--source", str(source_root)])
        elif action == "check":
            command.append("--check")
        elif action == "remove":
            command.append("--remove")
        else:
            raise ConsumerError(f"unsupported consumer action: {action}")

        result = subprocess.run(
            command,
            cwd=root,
            check=False,
        )
        if result.returncode != 0:
            raise ConsumerError(
                f"locked Boundary {action} failed with exit "
                f"status {result.returncode}"
            )


def _write_provenance(root: Path, lock: BoundaryLock) -> None:
    output = root / _PROVENANCE
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            lock.to_document(),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _require_provenance(root: Path, lock: BoundaryLock) -> None:
    path = root / _PROVENANCE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConsumerError(
            "installed Boundary source provenance is missing or invalid"
        ) from exc
    if value != lock.to_document():
        raise ConsumerError(
            "installed Boundary source does not match boundary.lock.json"
        )


def _git_exclude_path(root: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "info/exclude"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = " ".join((result.stderr or result.stdout).split())
        raise ConsumerError(
            "could not determine Git local exclude file"
            + (f": {detail}" if detail else "")
        )
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = root / path
    return path


def _update_local_excludes(root: Path, *, enabled: bool) -> None:
    path = _git_exclude_path(root)
    try:
        existing = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        existing = []

    lines = _without_managed_excludes(existing)
    while lines and not lines[-1]:
        lines.pop()

    if enabled:
        if lines:
            lines.append("")
        lines.append(_EXCLUDE_BEGIN)
        lines.extend(_GENERATED_EXCLUDES)
        lines.append(_EXCLUDE_END)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8",
    )


def _require_local_excludes(root: Path) -> None:
    path = _git_exclude_path(root)
    try:
        lines = set(path.read_text(encoding="utf-8").splitlines())
    except OSError as exc:
        raise ConsumerError(
            "Boundary generated-state Git exclusions are missing"
        ) from exc

    required = {
        _EXCLUDE_BEGIN,
        _EXCLUDE_END,
        *_GENERATED_EXCLUDES,
    }
    if not required.issubset(lines):
        raise ConsumerError(
            "Boundary generated-state Git exclusions are missing or stale"
        )


def _without_managed_excludes(lines: list[str]) -> list[str]:
    result: list[str] = []
    inside = False
    for line in lines:
        if line == _EXCLUDE_BEGIN:
            inside = True
            continue
        if line == _EXCLUDE_END:
            inside = False
            continue
        if not inside:
            result.append(line)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
