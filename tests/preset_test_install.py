import json
import tempfile
import unittest
from pathlib import Path

from preset_test_support import (
    EXTENSION_ROOT,
    INSTALLED_RUNTIME_PATH,
    INSTALLED_SCHEMA_PATH,
    PRESET_ROOT,
    SPECKIT_VERSION,
    WORKFLOW_OVERLAY_PATH,
    command_available,
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
HOOK_EVENTS = (
    "after_plan",
    "after_tasks",
    "before_implement",
    "after_implement",
)
WORKFLOW_STEPS = (
    "specdd-context",
    "specdd-task-validation",
    "specdd-authorize",
    "specdd-verify",
)
COMPOSED_EXPECTATIONS = {
    "speckit.plan": (
        "speckit.plan.md",
        "## Phases",
        "## SpecDD Planning Augmentation",
    ),
    "speckit.tasks": (
        "speckit.tasks.md",
        "## Task Generation Rules",
        "## SpecDD Task Augmentation",
    ),
    "speckit.converge": (
        "speckit.converge.md",
        "## Convergence Findings",
        "## SpecDD Convergence Augmentation",
    ),
}


@unittest.skipUnless(
    command_available("specify")
    and command_available("specdd")
    and command_available("git"),
    "Spec Kit, SpecDD, and Git are required for the preset install smoke test",
)
class PresetInstallTests(unittest.TestCase):
    def test_local_install_materializes_codex_commands_and_hooks(self):
        version = run_command(PRESET_ROOT, "specify", "--version")
        require_success(self, version)
        if SPECKIT_VERSION not in version.stdout + version.stderr:
            self.skipTest(
                f"Preset composition smoke requires Spec Kit {SPECKIT_VERSION}"
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            require_success(self, run_command(root, "git", "init", "-q"))
            require_success(
                self,
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
            baseline_bodies = {
                command: skill_body(
                    skill_file(root, command).read_text(encoding="utf-8")
                )
                for command in COMPOSED_EXPECTATIONS
            }

            require_success(
                self,
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
            overlay_list = run_command(
                root,
                "specify",
                "workflow",
                "overlay",
                "list",
                "speckit",
            )
            require_success(self, overlay_list)
            self.assertIn("specdd-bridge", overlay_list.stdout)

            resolved = run_command(
                root,
                "specify",
                "workflow",
                "resolve",
                "speckit",
            )
            require_success(self, resolved)
            for step in WORKFLOW_STEPS:
                self.assertIn(step, resolved.stdout)
            self.assertIn(str(INSTALLED_RUNTIME_PATH), resolved.stdout)

            order = (
                "plan",
                "specdd-context",
                "review-plan",
                "tasks",
                "specdd-task-validation",
                "specdd-authorize",
                "implement",
                "specdd-verify",
            )
            positions = [
                resolved.stdout.index(f"• {step}:")
                for step in order
            ]
            self.assertEqual(sorted(positions), positions)

            require_success(
                self,
                run_command(
                    root,
                    "specify",
                    "extension",
                    "add",
                    str(EXTENSION_ROOT),
                    "--dev",
                    "--force",
                ),
            )
            self.assertTrue((root / INSTALLED_RUNTIME_PATH).is_file())
            self.assertTrue((root / INSTALLED_SCHEMA_PATH).is_file())

            extension_list = run_command(
                root,
                "specify",
                "extension",
                "list",
                "--json",
            )
            require_success(self, extension_list)
            installed = {
                item["id"]: item
                for item in json.loads(extension_list.stdout)
            }
            self.assertIn("specdd", installed)
            self.assertTrue(installed["specdd"]["enabled"])
            self.assertEqual(4, installed["specdd"]["provides"]["commands"])
            self.assertEqual(4, installed["specdd"]["provides"]["hooks"])

            for command in BRIDGE_COMMANDS:
                with self.subTest(bridge_command=command):
                    self.assertTrue(skill_file(root, command).is_file())

            hook_state_path = root / ".specify" / "extensions.yml"
            hook_state = hook_state_path.read_text(encoding="utf-8")
            for event in HOOK_EVENTS:
                self.assertIn(f"{event}:", hook_state)
            for command in BRIDGE_COMMANDS:
                self.assertIn(command, hook_state)

            require_success(
                self,
                run_command(
                    root,
                    "specify",
                    "preset",
                    "add",
                    "--dev",
                    str(PRESET_ROOT),
                    "--priority",
                    "10",
                ),
            )
            preset_dir = root / ".specify" / "presets" / "specdd-bridge"
            composed_dir = preset_dir / ".composed"

            for command, markers in COMPOSED_EXPECTATIONS.items():
                with self.subTest(composed=command):
                    filename, upstream, augmentation = markers
                    contents = (
                        (composed_dir / filename).read_text(encoding="utf-8"),
                        skill_file(root, command).read_text(encoding="utf-8"),
                    )
                    for content in contents:
                        self.assertIn(upstream, content)
                        self.assertIn(augmentation, content)
                        self.assertLess(
                            content.index(upstream),
                            content.index(augmentation),
                        )

            require_success(
                self,
                run_command(
                    root,
                    "specify",
                    "preset",
                    "remove",
                    "specdd-bridge",
                ),
            )
            self.assertFalse(preset_dir.exists())

            for command, baseline_body in baseline_bodies.items():
                with self.subTest(core_skill_restored=command):
                    restored = skill_file(root, command).read_text(
                        encoding="utf-8"
                    )
                    self.assertEqual(baseline_body, skill_body(restored))
                    self.assertNotIn(
                        COMPOSED_EXPECTATIONS[command][2],
                        restored,
                    )

            require_success(
                self,
                run_command(
                    root,
                    "specify",
                    "extension",
                    "remove",
                    "specdd",
                    "--force",
                ),
            )
            self.assertFalse((root / INSTALLED_RUNTIME_PATH).exists())
            self.assertFalse((root / INSTALLED_SCHEMA_PATH).exists())

            extension_list = run_command(
                root,
                "specify",
                "extension",
                "list",
                "--json",
            )
            require_success(self, extension_list)
            remaining = {
                item["id"]
                for item in json.loads(extension_list.stdout)
            }
            self.assertNotIn("specdd", remaining)

            for command in BRIDGE_COMMANDS:
                with self.subTest(bridge_command_removed=command):
                    self.assertFalse(skill_file(root, command).exists())

            remaining_hook_state = (
                hook_state_path.read_text(encoding="utf-8")
                if hook_state_path.is_file()
                else ""
            )
            self.assertNotIn("speckit.specdd.", remaining_hook_state)

            require_success(
                self,
                run_command(
                    root,
                    "specify",
                    "workflow",
                    "overlay",
                    "remove",
                    "speckit",
                    "specdd-bridge",
                ),
            )
            overlay_list = run_command(
                root,
                "specify",
                "workflow",
                "overlay",
                "list",
                "speckit",
            )
            require_success(self, overlay_list)
            self.assertNotIn("specdd-bridge", overlay_list.stdout)
