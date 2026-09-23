import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary.authorization import (
    ChangeWriteSet,
    ContractEvolutionWriteSet,
    TaskWriteSet,
    authorize_contract_evolution_operation,
    authorize_implementation_operation,
    read_current_operation,
)
from boundary.verification import (
    VerificationError,
    finalize_operation_verification,
    verify_operation_authorization,
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


def write_source_contract(root: Path) -> None:
    path = root / "contracts" / "source.contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
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


def write_policy_contract(root: Path) -> None:
    path = root / "contracts" / "policy.contract.md"
    path.write_text(
        "---\n"
        "schema: boundary.contract/v1\n"
        "id: policy\n"
        "owns: []\n"
        "applies_to:\n"
        "  - src/**\n"
        "depends_on: []\n"
        "---\n"
        "## Invariants\n\n"
        "- New policy applies.\n",
        encoding="utf-8",
    )


def implementation_change(*paths: str) -> ChangeWriteSet:
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
class NativeVerificationTests(unittest.TestCase):
    def initialize(self, root: Path) -> None:
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "tests@example.invalid")
        run_git(root, "config", "user.name", "Boundary Tests")
        write_source_contract(root)
        source = root / "src"
        source.mkdir()
        (source / "a.py").write_text("VALUE = 'a'\n", encoding="utf-8")
        (source / "b.py").write_text("VALUE = 'b'\n", encoding="utf-8")
        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "baseline")

    def test_authorized_actual_write_closes_operation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                implementation_change("src/a.py"),
            )
            (root / "src" / "a.py").write_text(
                "VALUE = 'changed'\n",
                encoding="utf-8",
            )

            result = verify_operation_authorization(root)
            verified = finalize_operation_verification(root)

        self.assertEqual(("src/a.py",), result.actual_paths)
        self.assertFalse(result.blocking)
        self.assertEqual("verified", verified.status)

    def test_rejects_undeclared_write_in_same_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                implementation_change("src/a.py"),
            )
            (root / "src" / "b.py").write_text(
                "VALUE = 'undeclared'\n",
                encoding="utf-8",
            )

            with self.assertRaises(VerificationError) as raised:
                finalize_operation_verification(root)
            current = read_current_operation(root)

        self.assertEqual("UNDECLARED_WRITE", raised.exception.code)
        self.assertEqual("authorized", current.status)

    def test_rejects_native_contract_change_during_implementation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                implementation_change("src/a.py"),
            )
            write_policy_contract(root)

            with self.assertRaises(VerificationError) as raised:
                finalize_operation_verification(root)

        self.assertEqual("OPERATION_KIND_VIOLATION", raised.exception.code)

    def test_fresh_resolution_detects_changed_effective_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                implementation_change("src/a.py"),
            )
            (root / "src" / "a.py").write_text(
                "VALUE = 'changed'\n",
                encoding="utf-8",
            )
            write_policy_contract(root)

            result = verify_operation_authorization(root)

        codes = {item.code for item in result.diagnostics}
        self.assertIn("OPERATION_KIND_VIOLATION", codes)
        self.assertIn("CONTRACT_CONTEXT_CHANGED", codes)

    def test_unchanged_baseline_dirty_state_is_not_an_actual_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            note = root / "docs" / "note.md"
            note.parent.mkdir()
            note.write_text("preexisting\n", encoding="utf-8")
            authorize_implementation_operation(
                root,
                implementation_change("src/a.py"),
            )

            result = verify_operation_authorization(root)

        self.assertEqual((), result.actual_paths)
        self.assertFalse(result.blocking)

    def test_adapter_owned_generated_state_can_be_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_implementation_operation(
                root,
                implementation_change("src/a.py"),
            )
            generated = root / ".adapter" / "generated.json"
            generated.parent.mkdir()
            generated.write_text("{}\n", encoding="utf-8")

            result = verify_operation_authorization(
                root,
                classify_path=lambda path: (
                    "generated"
                    if path.startswith(".adapter/")
                    else "ordinary"
                ),
            )

        self.assertEqual((".adapter/generated.json",), result.excluded_paths)
        self.assertFalse(result.blocking)

    def test_contract_evolution_rejects_ordinary_project_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize(root)
            authorize_contract_evolution_operation(
                root,
                ContractEvolutionWriteSet(
                    "001-change",
                    ("contracts/source.contract.md",),
                ),
            )
            (root / "src" / "a.py").write_text(
                "VALUE = 'wrong-kind'\n",
                encoding="utf-8",
            )

            with self.assertRaises(VerificationError) as raised:
                finalize_operation_verification(root)

        self.assertEqual("OPERATION_KIND_VIOLATION", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
