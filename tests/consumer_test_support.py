"""Helpers for downstream consumer lifecycle tests."""

from __future__ import annotations

from contextlib import redirect_stderr
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Callable
import unittest

import consumer as consumer_module
from consumer_lock import BoundaryLock, write_lock


_REQUIRED_PLACEHOLDERS = (
    "integration/speckit/extension.yml",
    "integration/speckit-preset/preset.yml",
    "integration/speckit/workflow-overlay.yml",
    "adapters/codex/materialize.py",
    "scripts/install-host.sh",
    "scripts/install-source.sh",
    "scripts/consumer.py",
    "scripts/consumer_lock.py",
    "src/boundary/__init__.py",
    "skills/scope/SKILL.md",
    "skills/implement/SKILL.md",
    "skills/contracts/SKILL.md",
)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout


def make_archive(
    root: Path,
    revision: str,
    marker: str,
    *,
    fail_install: bool = False,
) -> tuple[BoundaryLock, Path]:
    source = root / f"boundary-{revision[:8]}"
    source.mkdir()
    for relative in _REQUIRED_PLACEHOLDERS:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    failure = "exit 23" if fail_install else ""
    (source / "scripts" / "install.sh").write_text(
        _installer_source(marker, failure),
        encoding="utf-8",
    )

    archive = root / f"{revision}.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(source, arcname=source.name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return (
        BoundaryLock(
            source_url=(
                "https://github.com/example/boundary/archive/"
                f"{revision}.tar.gz"
            ),
            revision=revision,
            sha256=digest,
        ),
        archive,
    )


def _installer_source(marker: str, failure: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -eu\n"
        f"readonly MARKER={marker!r}\n"
        "install_state() {\n"
        "  mkdir -p .agents/skills/{boundary-scope,boundary-implement,"
        "boundary-contracts,speckit-boundary-authorize,"
        "speckit-boundary-verify}\n"
        "  mkdir -p .specify/boundary-runtime "
        ".specify/extensions/boundary .specify/presets/boundary\n"
        "  mkdir -p .specify/workflows/overlays/speckit\n"
        "  printf '%s\\n' \"$MARKER\" > "
        ".specify/boundary-runtime/installed-version\n"
        "  for skill in boundary-scope boundary-implement "
        "boundary-contracts speckit-boundary-authorize "
        "speckit-boundary-verify; do\n"
        "    printf '%s\\n' \"$MARKER\" > "
        "\".agents/skills/${skill}/SKILL.md\"\n"
        "  done\n"
        "  printf '%s\\n' \"$MARKER\" > .specify/extensions/boundary/state\n"
        "  printf '%s\\n' \"$MARKER\" > .specify/presets/boundary/state\n"
        "  printf '%s\\n' \"$MARKER\" > "
        ".specify/workflows/overlays/speckit/boundary.yml\n"
        "  printf '{\"host\":\"baseline\",\"boundary\":\"%s\"}\\n' "
        "\"$MARKER\" > .specify/shared-registry.json\n"
        "}\n"
        "case \"${1:-}\" in\n"
        "  --source)\n"
        "    install_state\n"
        f"    {failure}\n"
        "    ;;\n"
        "  --check)\n"
        "    test \"$(cat .specify/boundary-runtime/installed-version)\" "
        "= \"$MARKER\"\n"
        "    ;;\n"
        "  --remove)\n"
        "    rm -rf .agents/skills/boundary-scope "
        ".agents/skills/boundary-implement "
        ".agents/skills/boundary-contracts "
        ".agents/skills/speckit-boundary-authorize "
        ".agents/skills/speckit-boundary-verify\n"
        "    rm -rf .specify/boundary-runtime "
        ".specify/extensions/boundary .specify/presets/boundary\n"
        "    rm -f .specify/workflows/overlays/speckit/boundary.yml\n"
        "    printf '{\"host\":\"baseline\"}\\n' > "
        ".specify/shared-registry.json\n"
        "    ;;\n"
        "  *) exit 64 ;;\n"
        "esac\n"
    )


def initialize_fixture(root: Path, lock: BoundaryLock) -> None:
    run_git(root, "init", "-q")
    run_git(root, "config", "user.email", "tests@example.invalid")
    run_git(root, "config", "user.name", "Boundary Tests")
    write_lock(root / "boundary.lock.json", lock)
    contract = root / "contracts" / "app.contract.md"
    contract.parent.mkdir(parents=True)
    contract.write_text("fixture contract\n", encoding="utf-8")
    registry = root / ".specify" / "shared-registry.json"
    registry.parent.mkdir(parents=True)
    registry.write_text('{"host":"baseline"}\n', encoding="utf-8")
    run_git(root, "add", "-A")
    run_git(root, "commit", "-q", "-m", "consumer fixture")


def clone_fixture(source: Path, target: Path) -> None:
    result = subprocess.run(
        ["git", "clone", "-q", "--local", str(source), str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)


def download_from(
    archives: dict[str, Path],
) -> Callable[[str, Path], None]:
    def download(url: str, output: Path) -> None:
        shutil.copyfile(archives[url], output)

    return download


def run_consumer(root: Path, *args: str) -> int:
    with redirect_stderr(io.StringIO()):
        return consumer_module.main(["--root", str(root), *args])


def status_paths(root: Path) -> tuple[str, ...]:
    output = run_git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    return tuple(line[3:] for line in output.splitlines())


def assert_no_boundary_generated_status(
    case: unittest.TestCase,
    root: Path,
) -> None:
    generated_roots = tuple(
        value.strip("/")
        for value in consumer_module._GENERATED_EXCLUDES
    )
    for path in status_paths(root):
        case.assertFalse(
            any(
                path == generated
                or path.startswith(f"{generated}/")
                for generated in generated_roots
            ),
            path,
        )
