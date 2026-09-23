from pathlib import Path
import sys
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from boundary.contracts import (
    Contract,
    ContractDependencyError,
    ContractGraphError,
    ContractOwnershipError,
    ContractSections,
    ScopeClaim,
    build_contract_graph,
    scope_matches,
    scope_strictly_contains,
    scopes_overlap,
)


def contract(
    contract_id: str,
    *,
    owns: tuple[str, ...] = (),
    applies_to: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
) -> Contract:
    return Contract(
        contract_id=contract_id,
        source_path=f"contracts/{contract_id}.contract.md",
        owns=owns,
        applies_to=applies_to,
        depends_on=depends_on,
        sections=ContractSections(),
        content_identity=f"sha256:{contract_id}",
    )


class ContractScopeRelationTests(unittest.TestCase):
    def test_exact_and_subtree_matching_does_not_consult_filesystem(self):
        self.assertTrue(
            scope_matches(
                "src/auth/service.py",
                "src/auth/service.py",
            )
        )
        self.assertFalse(
            scope_matches(
                "src/auth/service.py",
                "src/auth/missing.py",
            )
        )
        self.assertTrue(
            scope_matches(
                "src/auth/**",
                "src/auth",
            )
        )
        self.assertTrue(
            scope_matches(
                "src/auth/**",
                "src/auth/missing.py",
            )
        )
        self.assertFalse(
            scope_matches(
                "src/auth/**",
                "src/authz/service.py",
            )
        )

    def test_scope_relationships_are_structural(self):
        self.assertTrue(
            scope_strictly_contains(
                "src/**",
                "src/auth/**",
            )
        )
        self.assertTrue(
            scope_strictly_contains(
                "src/auth/**",
                "src/auth/service.py",
            )
        )
        self.assertTrue(
            scopes_overlap(
                "src/auth/**",
                "src/auth/service.py",
            )
        )
        self.assertFalse(
            scopes_overlap(
                "src/auth/**",
                "src/users/**",
            )
        )


class ContractGraphTests(unittest.TestCase):
    def test_builds_deterministic_graph_indexes(self):
        auth = contract(
            "auth",
            owns=("src/auth/**",),
            applies_to=("src/api/session.py",),
            depends_on=("users",),
        )
        users = contract(
            "users",
            owns=("src/users/**",),
        )

        graph = build_contract_graph((users, auth))

        self.assertEqual(
            ("auth", "users"),
            tuple(
                item.contract_id
                for item in graph.contracts
            ),
        )
        self.assertEqual(
            (
                ("auth", auth),
                ("users", users),
            ),
            graph.contracts_by_id,
        )
        self.assertEqual(
            (
                ScopeClaim("src/auth/**", "auth"),
                ScopeClaim("src/users/**", "users"),
            ),
            graph.ownership_scopes,
        )
        self.assertEqual(
            (
                ScopeClaim("src/api/session.py", "auth"),
                ScopeClaim("src/auth/**", "auth"),
                ScopeClaim("src/users/**", "users"),
            ),
            graph.applicability_scopes,
        )
        self.assertEqual(
            (("auth", "users"),),
            graph.dependency_edges,
        )
        self.assertEqual(
            graph,
            build_contract_graph((auth, users)),
        )

    def test_allows_strictly_nested_ownership(self):
        graph = build_contract_graph(
            (
                contract(
                    "payments",
                    owns=("src/payments/**",),
                ),
                contract(
                    "stripe",
                    owns=("src/payments/providers/stripe/**",),
                ),
                contract(
                    "manifest",
                    owns=("src/payments/manifest.json",),
                ),
            )
        )

        self.assertEqual(
            3,
            len(graph.ownership_scopes),
        )

    def test_rejects_equal_ownership_claims_from_different_contracts(self):
        with self.assertRaises(ContractOwnershipError):
            build_contract_graph(
                (
                    contract(
                        "alpha",
                        owns=("src/shared/**",),
                    ),
                    contract(
                        "beta",
                        owns=("src/shared/**",),
                    ),
                )
            )

    def test_rejects_duplicate_contract_ids(self):
        with self.assertRaises(ContractGraphError):
            build_contract_graph(
                (
                    contract(
                        "duplicate",
                        owns=("src/a/**",),
                    ),
                    contract(
                        "duplicate",
                        owns=("src/b/**",),
                    ),
                )
            )

    def test_rejects_missing_and_self_dependencies(self):
        with self.assertRaises(ContractDependencyError):
            build_contract_graph(
                (
                    contract(
                        "auth",
                        owns=("src/auth/**",),
                        depends_on=("users",),
                    ),
                )
            )

        with self.assertRaises(ContractDependencyError):
            build_contract_graph(
                (
                    contract(
                        "auth",
                        owns=("src/auth/**",),
                        depends_on=("auth",),
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()
