from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_ROOT = REPO_ROOT / "integration" / "specdd-preset"
EXTENSION_ROOT = REPO_ROOT / "integration" / "specdd"
WORKFLOW_OVERLAY_PATH = (
    EXTENSION_ROOT
    / "workflow-overlay.yml"
)
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


def skill_body(content: str) -> str:
    """Return semantic command body, ignoring Codex registrar serialization."""
    lines = content.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                content = "".join(lines[index + 1 :])
                break

    content = content.lstrip("\r\n")
    body_lines = content.splitlines(keepends=True)
    if (
        body_lines
        and body_lines[0].startswith("# Speckit ")
        and body_lines[0].strip().endswith(" Skill")
    ):
        content = "".join(body_lines[1:]).lstrip("\r\n")

    return content


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
