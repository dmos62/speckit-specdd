import json
import tempfile
import unittest
from pathlib import Path

from preset_test_support import (
    EXTENSION_ROOT,
    GENERIC_COMMANDS_DIR,
    PRESET_ROOT,
    command_available,
    require_success,
    run_command,
)


@unittest.skipUnless(
    command_available("specify")
    and command_available("specdd")
    and command_available("git"),
    "Spec Kit, SpecDD, and Git are required for the preset install smoke test",
)
class PresetInstallTests(unittest.TestCase):
    def test_local_install_composes_and_uninstall_restores_core_commands(self):
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
                    "generic",
                    "--integration-options=--commands-dir .specify-agent/commands",
                ),
            )
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
                3,
                installed_extensions["specdd"]["provides"]["commands"],
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

            expectations = {
                "speckit.plan.md": (
                    "## Phases",
                    "## SpecDD Planning Augmentation",
                ),
                "speckit.tasks.md": (
                    "## Task Generation Rules",
                    "## SpecDD Task Augmentation",
                ),
                "speckit.converge.md": (
                    "## Convergence Findings",
                    "## SpecDD Convergence Augmentation",
                ),
            }
            for filename, markers in expectations.items():
                with self.subTest(filename=filename):
                    path = root / GENERIC_COMMANDS_DIR / filename
                    content = path.read_text(encoding="utf-8")
                    self.assertIn(markers[0], content)
                    self.assertIn(markers[1], content)
                    self.assertLess(
                        content.index(markers[0]),
                        content.index(markers[1]),
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
            for filename, markers in expectations.items():
                with self.subTest(restored=filename):
                    content = (
                        root / GENERIC_COMMANDS_DIR / filename
                    ).read_text(encoding="utf-8")
                    self.assertIn(markers[0], content)
                    self.assertNotIn(markers[1], content)

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
