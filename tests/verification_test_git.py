import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary_test_support import verification


class VerificationGitTests(unittest.TestCase):
    def git(
        self,
        root,
        *args,
    ):
        return subprocess.run(
            [
                "git",
                "-C",
                str(root),
                *args,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def initialize_repository(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(
            temporary.name
        ).resolve()

        self.git(
            root,
            "init",
        )
        self.git(
            root,
            "config",
            "user.name",
            "SpecDD Test",
        )
        self.git(
            root,
            "config",
            "user.email",
            "specdd@example.test",
        )

        files = {
            "src/auth/service.ts": "export const value = 1;\n",
            ".specify/generated.json": "{}\n",
            "specs/001-login/spec.md": "# Feature\n",
            "docs/old.md": "old\n",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            path.write_text(
                content,
                encoding="utf-8",
            )

        self.git(
            root,
            "add",
            ".",
        )
        self.git(
            root,
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "baseline",
        )
        return temporary, root

    def test_separates_actual_writes_from_nonimplementation_state(self):
        temporary, root = self.initialize_repository()
        with temporary:
            (root / "src/auth/service.ts").write_text(
                "export const value = 2;\n",
                encoding="utf-8",
            )
            (root / ".specify/generated.json").write_text(
                '{"changed": true}\n',
                encoding="utf-8",
            )
            (root / "specs/001-login/spec.md").write_text(
                "# Changed feature\n",
                encoding="utf-8",
            )

            new_write = root / "src/users/repository.ts"
            new_write.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            new_write.write_text(
                "export const repository = true;\n",
                encoding="utf-8",
            )

            new_spec = root / "src/auth/auth.sdd"
            new_spec.write_text(
                "Spec: Auth\n",
                encoding="utf-8",
            )

            changes = verification.collect_git_changes(
                root,
                feature_dir="specs/001-login",
            )

        self.assertEqual(
            [
                "src/auth/service.ts",
                "src/users/repository.ts",
            ],
            [
                item.path
                for item in changes.writes
            ],
        )
        self.assertEqual(
            ["src/auth/auth.sdd"],
            [
                item.path
                for item in changes.specs
            ],
        )
        self.assertEqual(
            ["specs/001-login/spec.md"],
            [
                item.path
                for item in changes.feature_artifacts
            ],
        )
        self.assertEqual(
            [".specify/generated.json"],
            [
                item.path
                for item in changes.generated
            ],
        )

    def test_marks_deleted_project_file(self):
        temporary, root = self.initialize_repository()
        with temporary:
            (root / "docs/old.md").unlink()

            changes = verification.collect_git_changes(
                root,
                feature_dir="specs/001-login",
            )

        deleted = [
            item
            for item in changes.writes
            if item.path == "docs/old.md"
        ]
        self.assertEqual(
            1,
            len(deleted),
        )
        self.assertTrue(
            deleted[0].deleted
        )
        self.assertEqual(
            "DELETED",
            deleted[0].status,
        )

    def test_missing_git_is_explicit_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()

            def missing_git(*args, **kwargs):
                raise FileNotFoundError("git")

            with self.assertRaisesRegex(
                verification.VerificationError,
                "Required Git executable was not found",
            ) as raised:
                verification.collect_git_changes(
                    root,
                    runner=missing_git,
                )

        self.assertIn(
            "bash scripts/bootstrap.sh --check",
            str(raised.exception),
        )
