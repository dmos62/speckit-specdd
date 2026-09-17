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
    skill_file,
)


@unittest.skipUnless(
    command_available("specify")
    and command_available("specdd")
    and command_available("git"),
    "Spec Kit, SpecDD, and Git are required for the preset install smoke test",
)
class PresetInstallTests(unittest.TestCase):
    def test_local_install_materializes_codex_commands_and_hooks(self):
        version = run_command(
            PRESET_ROOT,
            "specify",
            "--version",
        )
        require_success(self, version)
        if "1.0.7" not in version.stdout + version.stderr:
            self.skipTest(
                "Preset composition smoke requires Spec Kit 1.0.7"
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            require_success(
                self,
                run_command(
                    root,
                    "git",
                    "init",
                    "-q",
                ),
            )
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

            expectations = {
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
            baseline_skills = {
                command: skill_file(
                    root,
                    command,
                ).read_text(encoding="utf-8")
                for command in expectations
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
            require_success(
                self,
                extension_list,
            )
            installed_extensions = {
                item["id"]: item
                for item in json.loads(
                    extension_list.stdout
                )
            }
            self.assertIn(
                "specdd",
                installed_extensions,
            )
            self.assertTrue(
                installed_extensions["specdd"]["enabled"]
            )
            self.assertEqual(
                4,
                installed_extensions["specdd"]["provides"]["commands"],
            )
            self.assertEqual(
                4,
                installed_extensions["specdd"]["provides"]["hooks"],
            )

            bridge_commands = (
                "speckit.specdd.context",
                "speckit.specdd.validate",
                "speckit.specdd.authorize",
                "speckit.specdd.verify",
            )
            for command in bridge_commands:
                with self.subTest(
                    bridge_command=command
                ):
                    self.assertTrue(
                        skill_file(
                            root,
                            command,
                        ).is_file()
                    )

            hook_state_path = (
                root
                / ".specify"
                / "extensions.yml"
            )
            hook_state = hook_state_path.read_text(
                encoding="utf-8"
            )
            for event in (
                "after_plan",
                "after_tasks",
                "before_implement",
                "after_implement",
            ):
                self.assertIn(
                    f"{event}:",
                    hook_state,
                )
            for command in bridge_commands:
                self.assertIn(
                    command,
                    hook_state,
                )

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

            preset_dir = (
                root
                / ".specify"
                / "presets"
                / "specdd-bridge"
            )
            composed_dir = preset_dir / ".composed"

            for command, markers in expectations.items():
                with self.subTest(
                    composed=command
                ):
                    filename, upstream, augmentation = markers
                    composed = (
                        composed_dir / filename
                    ).read_text(encoding="utf-8")
                    materialized = skill_file(
                        root,
                        command,
                    ).read_text(encoding="utf-8")

                    for content in (
                        composed,
                        materialized,
                    ):
                        self.assertIn(
                            upstream,
                            content,
                        )
                        self.assertIn(
                            augmentation,
                            content,
                        )
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
            self.assertFalse(
                preset_dir.exists()
            )

            for command, baseline in baseline_skills.items():
                with self.subTest(
                    core_skill_restored=command
                ):
                    self.assertEqual(
                        baseline,
                        skill_file(
                            root,
                            command,
                        ).read_text(encoding="utf-8"),
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
            require_success(
                self,
                extension_list,
            )
            remaining_extensions = {
                item["id"]
                for item in json.loads(
                    extension_list.stdout
                )
            }
            self.assertNotIn(
                "specdd",
                remaining_extensions,
            )

            for command in bridge_commands:
                with self.subTest(
                    bridge_command_removed=command
                ):
                    self.assertFalse(
                        skill_file(
                            root,
                            command,
                        ).exists()
                    )

            remaining_hook_state = (
                hook_state_path.read_text(
                    encoding="utf-8"
                )
                if hook_state_path.is_file()
                else ""
            )
            self.assertNotIn(
                "speckit.specdd.",
                remaining_hook_state,
            )
