import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary.authorization import (
    AuthorizationError,
    ChangeWriteSet,
    TaskWriteSet,
    authorize_implementation_operation,
    operation_archive_path,
    read_current_operation,
)
from boundary.verification import (
    VerificationError,
    finalize_operation_verification,
)


def run_git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)


def write_contract(root: Path) -> None:
    path = root / "contracts" / "source.contract.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\n"
        "schema: boundary.contract/v1\n"
        "id: source\n"
        "owns:\n"
        "  - src/**\n"
        "applies_to: []\n"
        "depends_on: []\n"
        "---\n"
        "## Purpose\n\n"
        "Own source implementation.\n\n"
        "## Invariants\n\n"
        "- Source behavior remains explicit.\n",
        encoding="utf-8",
    )


def change(*paths: str) -> ChangeWriteSet:
    return ChangeWriteSet(
        "001-change",
        (
            TaskWriteSet(
                0,
                "T001",
                "US1",
                tuple(paths),
            ),
        ),
    )


@unittest.skipUnless(shutil.which("git"), "Git is required")
class AuthorizationLifecycleTests(unittest.TestCase):
    def initialize(self, root: Path) -> None:
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "tests@example.invalid")
        run_git(root, "config", "user.name", "Boundary Tests")
        write_contract(root)

        source = root / "src"
        source.mkdir()
        (source / "a.py").write_text("VALUE = 'a'\n", encoding="utf-8")
        (source / "b.py").write_text("VALUE = 'b'\n", encoding="utf-8")
        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "baseline")

    def test_rejects_implementation_written_before_authorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            (root / "src" / "a.py").write_text(
                "VALUE = 'dirty'\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AuthorizationError,
                "DIRTY_TARGET_NOT_VERIFIED",
            ):
                authorize_implementation_operation(
                    root,
                    change("src/a.py"),
                )

    def test_requires_verification_before_reauthorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                change("src/a.py"),
            )

            with self.assertRaisesRegex(
                AuthorizationError,
                "OPERATION_NOT_VERIFIED",
            ):
                authorize_implementation_operation(
                    root,
                    change("src/b.py"),
                )

    def test_scope_expansion_carries_verified_output_and_archives_predecessor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            first = authorize_implementation_operation(
                root,
                change("src/a.py"),
            )
            (root / "src" / "a.py").write_text(
                "VALUE = 'first'\n",
                encoding="utf-8",
            )
            verified = finalize_operation_verification(
                root,
                operation_id=first.operation_id,
            )
            archive = operation_archive_path(
                root,
                first.operation_id,
            )
            self.assertFalse(archive.exists())

            second = authorize_implementation_operation(
                root,
                change("src/a.py", "src/b.py"),
            )

            self.assertTrue(archive.is_file())
            self.assertEqual("verified", verified.status)
            self.assertEqual(
                ("src/a.py",),
                tuple(item.path for item in second.carried_forward),
            )
            self.assertEqual(
                first.operation_id,
                second.carried_forward[0].operation_id,
            )

    def test_verified_predecessor_without_carry_is_not_archived(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            first = authorize_implementation_operation(
                root,
                change("src/a.py"),
            )
            finalize_operation_verification(root)

            authorize_implementation_operation(
                root,
                change("src/b.py"),
            )

            self.assertFalse(
                operation_archive_path(
                    root,
                    first.operation_id,
                ).exists()
            )

    def test_rejects_dirty_state_changed_after_predecessor_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                change("src/a.py"),
            )
            path = root / "src" / "a.py"
            path.write_text("VALUE = 'verified'\n", encoding="utf-8")
            finalize_operation_verification(root)
            path.write_text("VALUE = 'changed-again'\n", encoding="utf-8")

            with self.assertRaisesRegex(
                AuthorizationError,
                "DIRTY_TARGET_NOT_VERIFIED",
            ):
                authorize_implementation_operation(
                    root,
                    change("src/a.py"),
                )

    def test_deleted_verified_output_can_be_carried_forward(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                change("src/a.py"),
            )
            (root / "src" / "a.py").unlink()
            verified = finalize_operation_verification(root)

            successor = authorize_implementation_operation(
                root,
                change("src/a.py"),
            )

            self.assertEqual(
                verified.verification_final_states[0].state,
                successor.carried_forward[0].state,
            )

    def test_index_transition_invalidates_staged_predecessor_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                change("src/a.py"),
            )
            path = root / "src" / "a.py"
            path.write_text("VALUE = 'staged'\n", encoding="utf-8")
            run_git(root, "add", "src/a.py")
            finalize_operation_verification(root)

            run_git(root, "reset", "HEAD", "--", "src/a.py")

            with self.assertRaisesRegex(
                AuthorizationError,
                "DIRTY_TARGET_NOT_VERIFIED",
            ):
                authorize_implementation_operation(
                    root,
                    change("src/a.py"),
                )

    def test_head_change_blocks_verification_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                change("src/a.py"),
            )
            run_git(
                root,
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "move head",
            )

            with self.assertRaisesRegex(
                VerificationError,
                "GIT_BASELINE_CHANGED",
            ):
                finalize_operation_verification(root)

            current = read_current_operation(root)
            self.assertIsNotNone(current)
            self.assertEqual("authorized", current.status)


if __name__ == "__main__":
    unittest.main()
