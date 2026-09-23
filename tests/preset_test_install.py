import tempfile
import unittest
from pathlib import Path

from preset_test_install_support import (
    initialize_codex_project,
    install_extension,
    install_preset,
    install_workflow_overlay,
    remove_extension,
    remove_preset,
    remove_workflow_overlay,
)
from preset_test_support import (
    PRESET_ROOT,
    SPECKIT_VERSION,
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
    def test_local_install_materializes_codex_commands_and_hooks(self):
        version = run_command(PRESET_ROOT, "specify", "--version")
        require_success(self, version)
        if SPECKIT_VERSION not in version.stdout + version.stderr:
            self.skipTest(
                f"Preset composition smoke requires Spec Kit {SPECKIT_VERSION}"
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            baseline_bodies = initialize_codex_project(self, root)
            install_workflow_overlay(self, root)
            hook_state_path = install_extension(self, root)
            preset_dir = install_preset(self, root)
            remove_preset(self, root, preset_dir, baseline_bodies)
            remove_extension(self, root, hook_state_path)
            remove_workflow_overlay(self, root)
