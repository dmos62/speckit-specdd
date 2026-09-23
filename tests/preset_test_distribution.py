import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from preset_test_support import (
    EXTENSION_ROOT,
    INSTALLER_PATH,
    PRESET_ROOT,
    command_available,
    require_success,
    run_command,
)


@unittest.skipUnless(
    command_available("bash")
    and command_available("specify")
    and command_available("specdd")
    and command_available("codex")
    and command_available("git"),
    "Bash, Spec Kit, SpecDD, Codex, and Git are required for distribution tests",
)
class DistributionInstallTests(unittest.TestCase):
    def _init_project(
        self,
        root: Path,
        integration: str = "codex",
    ) -> None:
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
                integration,
            ),
        )

    def _active_integration(
        self,
        root: Path,
    ) -> str | None:
        state = json.loads(
            (
                root
                / ".specify"
                / "integration.json"
            ).read_text(encoding="utf-8")
        )
        return (
            state.get("default_integration")
            or state.get("integration")
        )

    def _assert_bridge_installed(
        self,
        root: Path,
    ) -> None:
        self.assertTrue(
            (
                root
                / ".specify"
                / "extensions"
                / "specdd"
            ).is_dir()
        )
        self.assertTrue(
            (
                root
                / ".specify"
                / "presets"
                / "specdd-bridge"
            ).is_dir()
        )

        overlay = run_command(
            root,
            "specify",
            "workflow",
            "overlay",
            "list",
            "speckit",
        )
        require_success(self, overlay)
        self.assertIn(
            "specdd-bridge",
            overlay.stdout,
        )

    def _archive_source(
        self,
        destination: Path,
    ) -> Path:
        archive = destination / "speckit-boundary-v0.1.0.tar.gz"
        prefix = "speckit-boundary-v0.1.0"

        with tarfile.open(
            archive,
            "w:gz",
        ) as package:
            package.add(
                EXTENSION_ROOT,
                arcname=f"{prefix}/integration/specdd",
            )
            package.add(
                PRESET_ROOT,
                arcname=f"{prefix}/integration/specdd-preset",
            )

        return archive

    def _fake_curl(
        self,
        root: Path,
    ) -> Path:
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

    def test_local_install_switches_codex_and_supports_remove_reinstall(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self._init_project(
                root,
                integration="claude",
            )

            first = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--source",
                str(INSTALLER_PATH.parents[1]),
            )
            require_success(self, first)
            self.assertEqual(
                "codex",
                self._active_integration(root),
            )
            self._assert_bridge_installed(root)

            check = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--check",
            )
            require_success(self, check)

            removed = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--remove",
            )
            require_success(self, removed)
            self.assertFalse(
                (
                    root
                    / ".specify"
                    / "extensions"
                    / "specdd"
                ).exists()
            )
            self.assertFalse(
                (
                    root
                    / ".specify"
                    / "presets"
                    / "specdd-bridge"
                ).exists()
            )

            second = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--source",
                str(INSTALLER_PATH.parents[1]),
            )
            require_success(self, second)
            self._assert_bridge_installed(root)

    def test_immutable_github_archive_uses_remote_install_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self._init_project(root)

            archive = self._archive_source(root)
            fake_bin = self._fake_curl(root)
            env = {
                "PATH": (
                    str(fake_bin)
                    + os.pathsep
                    + os.environ["PATH"]
                ),
                "SPECKIT_BOUNDARY_TEST_ARCHIVE": str(archive),
            }
            source = (
                "https://github.com/specdd/speckit-boundary/"
                "archive/refs/tags/v0.1.0.tar.gz"
            )

            installed = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--source",
                source,
                env=env,
            )
            require_success(self, installed)
            self._assert_bridge_installed(root)

            resolved = run_command(
                root,
                "specify",
                "workflow",
                "resolve",
                "speckit",
            )
            require_success(self, resolved)
            for step in (
                "specdd-context",
                "specdd-task-validation",
                "specdd-authorize",
                "specdd-verify",
            ):
                self.assertIn(
                    step,
                    resolved.stdout,
                )

    def test_mutable_github_branch_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = (
                "https://github.com/specdd/speckit-boundary/"
                "archive/refs/heads/main.tar.gz"
            )

            result = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--source",
                source,
            )

            self.assertNotEqual(
                0,
                result.returncode,
            )
            self.assertIn(
                "immutable GitHub",
                result.stderr,
            )
