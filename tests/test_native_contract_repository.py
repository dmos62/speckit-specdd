"""Repository-level coverage for canonical native Boundary contracts."""

from pathlib import Path
import unittest

from boundary.contracts import load_contract_graph
from boundary.context import resolve_target_context


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class RepositoryNativeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = load_contract_graph(REPOSITORY_ROOT)

    def test_representative_repository_paths_have_expected_owners(self) -> None:
        expected = {
            "src/boundary/repository/paths.py": "boundary-repository",
            "src/boundary/contracts/parser.py": "boundary-native-contracts",
            "src/boundary/context/resolver.py": "boundary-context",
            "src/boundary/authorization/service.py": "boundary-authorization",
            "src/boundary/verification/service.py": "boundary-verification",
            "src/boundary/cli/main.py": "boundary-cli",
            "adapters/codex/materialize.py": "boundary-agent-adapters",
            "skills/implement/SKILL.md": "boundary-agent-procedure",
            "scripts/bootstrap.sh": "boundary-repository-tooling",
            "README.md": "boundary-documentation",
            "docs/spec.md": "boundary-specifications",
            "docs/TODO.md": "boundary-documentation",
            "tests/test_native_contract_graph.py": "boundary-tests",
            "integration/specdd/scripts/boundary.py": (
                "boundary-change-adapter-migration"
            ),
        }

        for path, owner in expected.items():
            with self.subTest(path=path):
                context = resolve_target_context(self.graph, path)
                self.assertEqual(context.owner_id, owner)

    def test_nested_core_ownership_keeps_broader_constraints_applicable(
        self,
    ) -> None:
        context = resolve_target_context(
            self.graph,
            "src/boundary/authorization/service.py",
        )

        self.assertEqual(context.owner_id, "boundary-authorization")
        self.assertTrue(
            {
                "boundary-core",
                "boundary-authorization",
                "boundary-operation-lifecycle",
            }.issubset(context.applicable_contract_ids)
        )

    def test_nested_spec_ownership_keeps_documentation_contract_applicable(
        self,
    ) -> None:
        context = resolve_target_context(
            self.graph,
            "docs/spec-contracts.md",
        )

        self.assertEqual(context.owner_id, "boundary-specifications")
        self.assertIn(
            "boundary-documentation",
            context.applicable_contract_ids,
        )

    def test_repository_contracts_do_not_use_global_catch_all_scope(
        self,
    ) -> None:
        for contract in self.graph.contracts:
            with self.subTest(contract=contract.contract_id):
                self.assertNotIn("**", contract.owns)
                self.assertNotIn("**", contract.applies_to)


if __name__ == "__main__":
    unittest.main()
