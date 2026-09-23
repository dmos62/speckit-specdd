from __future__ import annotations

import json
from pathlib import Path

from preset_test_support import (
    EXTENSION_ROOT,
    INSTALLED_RUNTIME_PATH,
    INSTALLED_SCHEMA_PATH,
    PRESET_ROOT,
    WORKFLOW_OVERLAY_PATH,
    require_success,
    run_command,
    skill_body,
    skill_file,
)

BRIDGE_COMMANDS = (
    "speckit.specdd.context",
    "speckit.specdd.validate",
    "speckit.specdd.authorize",
    "speckit.specdd.verify",
)
HOOK_EVENTS = ("after_plan", "after_tasks", "before_implement", "after_implement")
WORKFLOW_STEPS = (
    "specdd-context",
    "specdd-task-validation",
    "specdd-authorize",
    "specdd-verify",
)
WORKFLOW_ORDER = (
    "plan",
    "specdd-context",
    "review-plan",
    "tasks",
    "specdd-task-validation",
    "specdd-authorize",
    "implement",
    "specdd-verify",
)
COMPOSED_EXPECTATIONS = {
    "speckit.plan": ("speckit.plan.md", "## Phases", "## SpecDD Planning Augmentation"),
    "speckit.tasks": ("speckit.tasks.md", "## Task Generation Rules", "## SpecDD Task Augmentation"),
    "speckit.converge": ("speckit.converge.md", "## Convergence Findings", "## SpecDD Convergence Augmentation"),
}


def installed_overlay_text(root: Path) -> str:
    overlay_root = root / ".specify" / "workflows" / "overlays"
    matches: list[str] = []
    for path in overlay_root.rglob("*") if overlay_root.is_dir() else ():
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if str(INSTALLED_RUNTIME_PATH) in content and all(
            step in content for step in WORKFLOW_STEPS
        ):
            matches.append(content)
    if len(matches) != 1:
        raise AssertionError(
            f"expected one installed SpecDD workflow overlay, found {len(matches)}"
        )
    return matches[0]


def assert_resolved_workflow(testcase, output: str) -> None:
    for step in WORKFLOW_STEPS:
        testcase.assertIn(f"• {step}: project:specdd-bridge", output)
    positions = [output.index(f"• {step}:") for step in WORKFLOW_ORDER]
    testcase.assertEqual(sorted(positions), positions)


def initialize_codex_project(testcase, root: Path) -> dict[str, str]:
    require_success(testcase, run_command(root, "git", "init", "-q"))
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
            "codex",
        ),
    )
    return {
        command: skill_body(skill_file(root, command).read_text(encoding="utf-8"))
        for command in COMPOSED_EXPECTATIONS
    }


def install_workflow_overlay(testcase, root: Path) -> None:
    require_success(
        testcase,
        run_command(
            root,
            "specify",
            "workflow",
            "overlay",
            "add",
            str(WORKFLOW_OVERLAY_PATH),
            "--priority",
            "10",
        ),
    )
    overlay_list = run_command(root, "specify", "workflow", "overlay", "list", "speckit")
    require_success(testcase, overlay_list)
    testcase.assertIn("specdd-bridge", overlay_list.stdout)
    resolved = run_command(root, "specify", "workflow", "resolve", "speckit")
    require_success(testcase, resolved)
    assert_resolved_workflow(testcase, resolved.stdout)
    overlay_text = installed_overlay_text(root)
    testcase.assertIn(str(INSTALLED_RUNTIME_PATH), overlay_text)
    testcase.assertNotIn("integration/specdd/scripts/workflow_gate.py", overlay_text)


def install_extension(testcase, root: Path) -> Path:
    require_success(
        testcase,
        run_command(root, "specify", "extension", "add", str(EXTENSION_ROOT), "--dev", "--force"),
    )
    testcase.assertTrue((root / INSTALLED_RUNTIME_PATH).is_file())
    testcase.assertTrue((root / INSTALLED_SCHEMA_PATH).is_file())
    extension_list = run_command(root, "specify", "extension", "list", "--json")
    require_success(testcase, extension_list)
    installed = {item["id"]: item for item in json.loads(extension_list.stdout)}
    testcase.assertIn("specdd", installed)
    testcase.assertTrue(installed["specdd"]["enabled"])
    testcase.assertEqual(4, installed["specdd"]["provides"]["commands"])
    testcase.assertEqual(4, installed["specdd"]["provides"]["hooks"])
    for command in BRIDGE_COMMANDS:
        testcase.assertTrue(skill_file(root, command).is_file())
    hook_state_path = root / ".specify" / "extensions.yml"
    hook_state = hook_state_path.read_text(encoding="utf-8")
    for event in HOOK_EVENTS:
        testcase.assertIn(f"{event}:", hook_state)
    for command in BRIDGE_COMMANDS:
        testcase.assertIn(command, hook_state)
    return hook_state_path


def install_preset(testcase, root: Path) -> Path:
    require_success(
        testcase,
        run_command(root, "specify", "preset", "add", "--dev", str(PRESET_ROOT), "--priority", "10"),
    )
    preset_dir = root / ".specify" / "presets" / "specdd-bridge"
    composed_dir = preset_dir / ".composed"
    for command, markers in COMPOSED_EXPECTATIONS.items():
        filename, upstream, augmentation = markers
        contents = (
            (composed_dir / filename).read_text(encoding="utf-8"),
            skill_file(root, command).read_text(encoding="utf-8"),
        )
        for content in contents:
            testcase.assertIn(upstream, content)
            testcase.assertIn(augmentation, content)
            testcase.assertLess(content.index(upstream), content.index(augmentation))
    return preset_dir


def remove_preset(testcase, root: Path, preset_dir: Path, baseline_bodies: dict[str, str]) -> None:
    require_success(testcase, run_command(root, "specify", "preset", "remove", "specdd-bridge"))
    testcase.assertFalse(preset_dir.exists())
    for command, baseline_body in baseline_bodies.items():
        restored = skill_file(root, command).read_text(encoding="utf-8")
        testcase.assertEqual(baseline_body, skill_body(restored))
        testcase.assertNotIn(COMPOSED_EXPECTATIONS[command][2], restored)


def remove_extension(testcase, root: Path, hook_state_path: Path) -> None:
    require_success(
        testcase,
        run_command(root, "specify", "extension", "remove", "specdd", "--force"),
    )
    testcase.assertFalse((root / INSTALLED_RUNTIME_PATH).exists())
    testcase.assertFalse((root / INSTALLED_SCHEMA_PATH).exists())
    extension_list = run_command(root, "specify", "extension", "list", "--json")
    require_success(testcase, extension_list)
    remaining = {item["id"] for item in json.loads(extension_list.stdout)}
    testcase.assertNotIn("specdd", remaining)
    for command in BRIDGE_COMMANDS:
        testcase.assertFalse(skill_file(root, command).exists())
    remaining_hook_state = (
        hook_state_path.read_text(encoding="utf-8") if hook_state_path.is_file() else ""
    )
    testcase.assertNotIn("speckit.specdd.", remaining_hook_state)


def remove_workflow_overlay(testcase, root: Path) -> None:
    require_success(
        testcase,
        run_command(root, "specify", "workflow", "overlay", "remove", "speckit", "specdd-bridge"),
    )
    overlay_list = run_command(root, "specify", "workflow", "overlay", "list", "speckit")
    require_success(testcase, overlay_list)
    testcase.assertNotIn("specdd-bridge", overlay_list.stdout)
