import json
import os
import tempfile
import unittest
from pathlib import Path

from preset_test_support import (
    INSTALLER_PATH,
    INSTALLED_RUNTIME_PATH,
    INSTALLED_SCHEMA_PATH,
    active_integration,
    archive_source,
    command_available,
    fake_curl,
    init_project,
    require_success,
    run_command,
    run_installed_gate,
    write_consumer_fixture,
)


@unittest.skipUnless(
    command_available("bash")
    and command_available("specify")
    and command_available("specdd")
    and command_available("codex")
    and command_available("git")
    and command_available("uv"),
    "Bash, Spec Kit, SpecDD, Codex, Git, and uv are required for distribution tests",
)
class DistributionInstallTests(unittest.TestCase):
    def _assert_bridge_installed(self, root: Path) -> None:
        self.assertTrue(
            (root / ".specify" / "extensions" / "specdd").is_dir()
        )
        self.assertTrue(
            (root / ".specify" / "presets" / "specdd-bridge").is_dir()
        )
        self.assertTrue((root / INSTALLED_RUNTIME_PATH).is_file())
        self.assertTrue((root / INSTALLED_SCHEMA_PATH).is_file())

        overlay = run_command(
            root,
            "specify",
            "workflow",
            "overlay",
            "list",
            "speckit",
        )
        require_success(self, overlay)
        self.assertIn("specdd-bridge", overlay.stdout)

    def _install_remote_archive(
        self,
        root: Path,
        archive: Path,
    ):
        fake_bin = fake_curl(root)
        env = {
            "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
            "SPECKIT_BOUNDARY_TEST_ARCHIVE": str(archive),
        }
        source = (
            "https://github.com/specdd/speckit-boundary/"
            "archive/refs/tags/v0.1.0.tar.gz"
        )
        return run_command(
            root,
            "bash",
            str(INSTALLER_PATH),
            "--source",
            source,
            env=env,
        )

    def test_local_install_switches_codex_and_supports_remove_reinstall(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            init_project(self, root, integration="claude")

            first = run_command(
                root,
                "bash",
                str(INSTALLER_PATH),
                "--source",
                str(INSTALLER_PATH.parents[1]),
            )
            require_success(self, first)
            self.assertEqual("codex", active_integration(root))
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
                (root / ".specify" / "extensions" / "specdd").exists()
            )
            self.assertFalse(
                (root / ".specify" / "presets" / "specdd-bridge").exists()
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

    def test_immutable_archive_runs_lifecycle_without_vendored_bridge_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            init_project(self, root)
            feature_dir = write_consumer_fixture(self, root)
            archive = archive_source(root)

            installed = self._install_remote_archive(root, archive)
            require_success(self, installed)
            archive.unlink()
            self._assert_bridge_installed(root)

            self.assertFalse((root / "integration" / "specdd").exists())
            self.assertFalse((root / "integration" / "specdd-preset").exists())
            self.assertFalse((root / "scripts" / "bootstrap.sh").exists())

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
                self.assertIn(step, resolved.stdout)
            self.assertIn(
                str(INSTALLED_RUNTIME_PATH),
                resolved.stdout,
            )
            self.assertNotIn(
                "integration/specdd/scripts/workflow_gate.py",
                resolved.stdout,
            )

            context = run_installed_gate(root, feature_dir, "context")
            require_success(self, context)
            context_value = json.loads(context.stdout)
            self.assertEqual(
                "specs/001-runtime/.specdd/boundary.json",
                context_value["boundary"],
            )
            self.assertEqual(["src/app.py"], context_value["targets"])

            tasks = run_installed_gate(root, feature_dir, "tasks")
            require_success(self, tasks)
            task_value = json.loads(tasks.stdout)
            self.assertFalse(task_value["summary"]["blocking"])

            authorize = run_installed_gate(root, feature_dir, "authorize")
            require_success(self, authorize)
            authorization = json.loads(authorize.stdout)
            self.assertTrue(authorization["specddContextFresh"])
            self.assertTrue(
                authorization["authorizationSnapshot"]["stored"]
            )

            (root / "src" / "app.py").write_text(
                'VALUE = "after"\n',
                encoding="utf-8",
            )

            verify = run_installed_gate(root, feature_dir, "verify")
            require_success(self, verify)
            verification = json.loads(verify.stdout)
            self.assertFalse(verification["summary"]["blocking"])
            self.assertEqual(
                ["src/app.py"],
                [
                    item["path"]
                    for item in verification["changes"]["writeTargets"]
                ],
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

            self.assertNotEqual(0, result.returncode)
            self.assertIn("immutable GitHub", result.stderr)
