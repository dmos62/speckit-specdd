from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_ROOT = REPO_ROOT / "integration" / "specdd-preset"
EXTENSION_ROOT = REPO_ROOT / "integration" / "specdd"
BOOTSTRAP_PATH = REPO_ROOT / "scripts" / "bootstrap.sh"
CODEX_SKILLS_DIR = Path(".agents") / "skills"


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def skill_file(
    root: Path,
    command: str,
) -> Path:
    return (
        root
        / CODEX_SKILLS_DIR
        / command.replace(".", "-")
        / "SKILL.md"
    )


def run_command(
    root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def require_success(
    testcase,
    result: subprocess.CompletedProcess[str],
) -> None:
    testcase.assertEqual(
        0,
        result.returncode,
        result.stdout + "\n" + result.stderr,
    )
