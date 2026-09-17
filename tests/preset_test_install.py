import json
import tempfile
import unittest
from pathlib import Path

from preset_test_support import (
    EXTENSION_ROOT,
    PRESET_ROOT,
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
        if "1.0.7" not in version.stdout + version.stderr:
            self.skipTest("Preset composition smoke requires Spec Kit 1.0.7")

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
                    "extension",
                    "add",
                    str(EXTENSION_ROOT),
                    "--dev",
                    "--force",
                ),
            )
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
