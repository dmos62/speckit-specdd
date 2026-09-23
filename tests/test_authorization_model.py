import tempfile
import unittest
from pathlib import Path

from boundary.authorization import (
    AuthorizationError,
    ChangeWriteSet,
    ContractEvolutionWriteSet,
    TaskWriteSet,
    WriteSetError,
    authorize_contract_evolution,
    authorize_implementation,
)


def write_contract(
    root: Path,
    *,
    invariant: str = "Service behavior remains stable.",
) -> None:
    path = root / "contracts" / "auth.contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "schema: boundary.contract/v1\n"
        "id: auth\n"
        "owns:\n"
        "  - src/auth/**\n"
        "applies_to: []\n"
        "depends_on: []\n"
        "---\n"
        "## Purpose\n\n"
        "Own authentication implementation.\n\n"
        "## Invariants\n\n"
        f"- {invariant}\n",
        encoding="utf-8",
    )


class AuthorizationWriteSetTests(unittest.TestCase):
    def test_preserves_task_identity_order_and_exact_writes(self):
        first = TaskWriteSet(
            order=0,
            task_id="T010",
            story="US1",
            writes=("src/auth/service.ts", "src/users/repository.ts"),
        )
        second = TaskWriteSet(
            order=1,
            task_id="T011",
            story="US2",
            writes=("src/auth/service.ts", "docs/login.md"),
        )
        change = ChangeWriteSet(
            change_id="001-login",
            tasks=(first, second),
        )

        self.assertEqual((0, 1), tuple(task.order for task in change.tasks))
        self.assertEqual(("T010", "T011"), tuple(task.task_id for task in change.tasks))
        self.assertEqual(("US1", "US2"), tuple(task.story for task in change.tasks))
        self.assertEqual(
            (
                "src/auth/service.ts",
                "src/users/repository.ts",
                "docs/login.md",
            ),
            change.writes,
        )

    def test_rejects_noncanonical_or_duplicate_writes(self):
        with self.assertRaisesRegex(WriteSetError, "canonical repository syntax"):
            TaskWriteSet(
                order=0,
                task_id="T001",
                story="US1",
                writes=("src/auth/./service.ts",),
            )
        with self.assertRaisesRegex(WriteSetError, "duplicated"):
            TaskWriteSet(
                order=0,
                task_id="T001",
                story="US1",
                writes=("src/auth/service.ts", "src/auth/service.ts"),
            )

    def test_change_write_set_requires_canonical_task_order(self):
        later = TaskWriteSet(1, "T002", "US1", ("src/b.ts",))
        earlier = TaskWriteSet(0, "T001", "US1", ("src/a.ts",))
        with self.assertRaisesRegex(WriteSetError, "canonical task order"):
            ChangeWriteSet("001-change", (later, earlier))


class FreshAuthorizationTests(unittest.TestCase):
    def change(self, path: str) -> ChangeWriteSet:
        return ChangeWriteSet(
            "001-login",
            (
                TaskWriteSet(
                    0,
                    "T001",
                    "US1",
                    (path,),
                ),
            ),
        )

    def test_fresh_authorization_resolves_owner_and_context_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_contract(root)
            first = authorize_implementation(
                root,
                self.change("src/auth/service.ts"),
            )

            write_contract(
                root,
                invariant="Changed canonical behavior remains stable.",
            )
            second = authorize_implementation(
                root,
                self.change("src/auth/service.ts"),
            )

        self.assertEqual("auth", first.targets[0].owner_id)
        self.assertTrue(
            first.targets[0].effective_context_identity.startswith("sha256:")
        )
        self.assertNotEqual(
            first.targets[0].effective_context_identity,
            second.targets[0].effective_context_identity,
        )
        self.assertNotEqual(
            first.contract_graph_identity,
            second.contract_graph_identity,
        )

    def test_implementation_requires_one_unambiguous_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_contract(root)
            with self.assertRaisesRegex(
                AuthorizationError,
                "no primary owner",
            ):
                authorize_implementation(
                    root,
                    self.change("docs/login.md"),
                )

    def test_implementation_and_contract_evolution_are_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_contract(root)

            with self.assertRaisesRegex(
                AuthorizationError,
                "may not modify native contracts",
            ):
                authorize_implementation(
                    root,
                    self.change("contracts/auth.contract.md"),
                )

            evolution = authorize_contract_evolution(
                root,
                ContractEvolutionWriteSet(
                    "001-login",
                    ("contracts/auth.contract.md",),
                ),
            )
            self.assertEqual(
                ("contracts/auth.contract.md",),
                evolution.targets,
            )

            with self.assertRaisesRegex(
                AuthorizationError,
                "only native contracts",
            ):
                authorize_contract_evolution(
                    root,
                    ContractEvolutionWriteSet(
                        "001-login",
                        ("src/auth/service.ts",),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
