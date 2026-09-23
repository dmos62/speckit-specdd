from pathlib import Path
import sys
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from boundary.contracts import (
    Contract,
    ContractSections,
    build_contract_graph,
)
from boundary.context import resolve_target_context


def contract(
    contract_id: str,
    *,
    owns: tuple[str, ...] = (),
    applies_to: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
    sections: ContractSections | None = None,
) -> Contract:
    return Contract(
        contract_id=contract_id,
        source_path=f"contracts/{contract_id}.contract.md",
        owns=owns,
        applies_to=applies_to,
        depends_on=depends_on,
        sections=sections or ContractSections(),
        content_identity=f"sha256:{contract_id}",
    )


class TargetContextTests(unittest.TestCase):
    def test_exact_owner_is_selected_for_missing_intended_target(self):
        graph = build_contract_graph(
            (
                contract(
                    "manifest",
                    owns=("generated/new-manifest.json",),
                ),
            )
        )

        context = resolve_target_context(
            graph,
            "./generated/new-manifest.json",
        )

        self.assertEqual(
            "generated/new-manifest.json",
            context.target_path,
        )
        self.assertEqual(
            "manifest",
            context.owner_id,
        )
        self.assertEqual(
            ("manifest",),
            context.applicable_contract_ids,
        )

    def test_nested_owner_wins_while_broader_owners_remain_applicable(self):
        payments = contract(
            "payments",
            owns=("src/payments/**",),
            sections=ContractSections(
                invariants=("Never persist card data.",),
            ),
        )
        stripe = contract(
            "stripe",
            owns=("src/payments/providers/stripe/**",),
            sections=ContractSections(
                invariants=("Use Stripe adapters.",),
            ),
        )
        graph = build_contract_graph(
            (stripe, payments)
        )

        context = resolve_target_context(
            graph,
            "src/payments/providers/stripe/client.py",
        )

        self.assertEqual(
            "stripe",
            context.owner_id,
        )
        self.assertEqual(
            ("payments", "stripe"),
            context.applicable_contract_ids,
        )
        self.assertEqual(
            (
                "Never persist card data.",
                "Use Stripe adapters.",
            ),
            tuple(
                item.text
                for item in context.invariants
            ),
        )

    def test_applies_to_adds_context_without_ownership(self):
        api = contract(
            "api",
            owns=("src/api/**",),
        )
        relationship = contract(
            "auth-api",
            applies_to=("src/api/session.py",),
            sections=ContractSections(
                prohibitions=("Do not expose tokens.",),
            ),
        )
        graph = build_contract_graph(
            (relationship, api)
        )

        context = resolve_target_context(
            graph,
            "src/api/session.py",
        )

        self.assertEqual(
            "api",
            context.owner_id,
        )
        self.assertEqual(
            ("api", "auth-api"),
            context.applicable_contract_ids,
        )
        self.assertEqual(
            ("Do not expose tokens.",),
            tuple(
                item.text
                for item in context.prohibitions
            ),
        )

    def test_projects_applicable_and_direct_dependency_interfaces(self):
        users = contract(
            "users",
            owns=("src/users/**",),
            depends_on=("storage",),
            sections=ContractSections(
                interfaces=("Use UserIdentity.",),
            ),
        )
        storage = contract(
            "storage",
            owns=("src/storage/**",),
            sections=ContractSections(
                interfaces=("Use StorageGateway.",),
            ),
        )
        auth = contract(
            "auth",
            owns=("src/auth/**",),
            depends_on=("users",),
            sections=ContractSections(
                interfaces=("Use AuthSession.",),
            ),
        )
        graph = build_contract_graph(
            (storage, users, auth)
        )

        context = resolve_target_context(
            graph,
            "src/auth/new_service.py",
        )

        self.assertEqual(
            ("Use AuthSession.",),
            tuple(
                item.text
                for item in context.interfaces
            ),
        )
        self.assertEqual(
            ("Use UserIdentity.",),
            tuple(
                item.text
                for item in context.dependency_interfaces
            ),
        )
        self.assertEqual(
            ("users",),
            tuple(
                item.contract_id
                for item in context.dependency_interfaces
            ),
        )
        self.assertEqual(
            ("sha256:users",),
            tuple(
                item.content_identity
                for item in context.dependency_interfaces
            ),
        )
        self.assertEqual(
            ("contracts/users.contract.md",),
            tuple(
                item.source_path
                for item in context.dependency_interfaces
            ),
        )

    def test_resolution_is_deterministic_across_contract_input_order(self):
        broad = contract(
            "broad",
            owns=("src/domain/**",),
        )
        narrow = contract(
            "narrow",
            owns=("src/domain/nested/**",),
        )
        relation = contract(
            "relation",
            applies_to=("src/domain/nested/file.py",),
        )

        first = resolve_target_context(
            build_contract_graph(
                (broad, narrow, relation)
            ),
            "src/domain/nested/file.py",
        )
        second = resolve_target_context(
            build_contract_graph(
                (relation, narrow, broad)
            ),
            "src/domain/nested/file.py",
        )

        self.assertEqual(
            first,
            second,
        )


if __name__ == "__main__":
    unittest.main()
