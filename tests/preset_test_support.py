from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_ROOT = REPO_ROOT / "integration" / "specdd-preset"
EXTENSION_ROOT = REPO_ROOT / "integration" / "specdd"
WORKFLOW_OVERLAY_PATH = EXTENSION_ROOT / "workflow-overlay.yml"
BOOTSTRAP_PATH = REPO_ROOT / "scripts" / "bootstrap.sh"
INSTALLER_PATH = REPO_ROOT / "scripts" / "install.sh"
CODEX_SKILLS_DIR = Path(".agents") / "skills"
INSTALLED_RUNTIME_PATH = (
    Path(".specify")
    / "extensions"
    / "specdd"
    / "scripts"
    / "workflow_gate.py"
)
INSTALLED_SCHEMA_PATH = (
    Path(".specify")
    / "extensions"
    / "specdd"
    / "schemas"
    / "change-boundary.schema.json"
)

SPECKIT_VERSION = "1.0.10"
SPECDD_UPSTREAM_CLI_VERSION = "1.1.1"
SPECDD_PROVIDER_VERSION = "1.2.0"
SPECDD_FRAMEWORK_VERSION = "1.5"


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
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    return subprocess.run(
        list(args),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=process_env,
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


def init_project(
    testcase,
    root: Path,
    integration: str = "codex",
) -> None:
    require_success(
        testcase,
        run_command(root, "git", "init", "-q"),
    )
    require_success(
        testcase,
        run_command(
            root,
            "specify",
            "init",
            "--here",
            "--force",
            "--non-interactive",
            "--ignore-agent-tools",
            "--script",
            "ps",
            "--integration",
            integration,
        ),
    )


def active_integration(root: Path) -> str | None:
    state = json.loads(
        (root / ".specify" / "integration.json").read_text(
            encoding="utf-8"
        )
    )
    return state.get("default_integration") or state.get("integration")


def archive_source(destination: Path) -> Path:
    archive = destination / "speckit-boundary-v0.1.0.tar.gz"
    prefix = "speckit-boundary-v0.1.0"
    with tarfile.open(archive, "w:gz") as package:
        package.add(
            EXTENSION_ROOT,
            arcname=f"{prefix}/integration/specdd",
        )
        package.add(
            PRESET_ROOT,
            arcname=f"{prefix}/integration/specdd-preset",
        )
    return archive


def fake_curl(root: Path) -> Path:
    bin_dir = root / "fake-bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(
        """#!/usr/bin/env python3
import os
import shutil
import sys

args = sys.argv[1:]
target = args[args.index("-o") + 1]
shutil.copyfile(
    os.environ["SPECKIT_BOUNDARY_TEST_ARCHIVE"],
    target,
)
""",
        encoding="utf-8",
    )
    curl.chmod(0o755)
    return bin_dir


def write_consumer_fixture(testcase, root: Path) -> Path:
    require_success(
        testcase,
        run_command(
            root,
            "specdd",
            "init",
            "--version",
            SPECDD_FRAMEWORK_VERSION,
        ),
    )

    source = root / "src" / "app.py"
    source.parent.mkdir(parents=True)
    source.write_text('VALUE = "before"\n', encoding="utf-8")

    feature_dir = root / "specs" / "001-runtime"
    feature_dir.mkdir(parents=True)
    (feature_dir / "plan.md").write_text(
        "# Plan\n\nImplementation target: `src/app.py`\n",
        encoding="utf-8",
    )
    (feature_dir / "tasks.md").write_text(
        "# Tasks\n\n"
        "- [ ] T001 Update application value\n"
        "  Writes: `src/app.py`\n",
        encoding="utf-8",
    )

    (root / f"{root.name}.sdd").write_text(
        """Spec: Consumer Runtime Fixture

Purpose:
  Provide one implementation target for installed bridge lifecycle testing.

Owns:
  ./src/app.py

Must:
  The fixture value remains a string.
""",
        encoding="utf-8",
    )

    for key, value in (
        ("user.email", "tests@example.invalid"),
        ("user.name", "Spec Kit Boundary Tests"),
    ):
        require_success(
            testcase,
            run_command(root, "git", "config", key, value),
        )
    require_success(testcase, run_command(root, "git", "add", "-A"))
    require_success(
        testcase,
        run_command(
            root,
            "git",
            "commit",
            "-q",
            "-m",
            "consumer fixture baseline",
        ),
    )
    return feature_dir


def run_installed_gate(
    root: Path,
    feature_dir: Path,
    stage: str,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        root,
        "uv",
        "run",
        "--no-project",
        "python",
        str(INSTALLED_RUNTIME_PATH),
        stage,
        env={
            "SPECIFY_FEATURE_DIRECTORY": feature_dir.relative_to(root).as_posix()
        },
    )
