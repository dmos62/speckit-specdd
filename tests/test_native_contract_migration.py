from pathlib import Path
import shutil
import sys
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from boundary.contracts import load_contract_graph
from boundary.context import resolve_target_context
from boundary_test_support import (
    FIXTURE_ROOT,
    REPO_ROOT,
    boundary as legacy_boundary,
)


LEGACY_OWNER_IDS = {
    "src/auth/auth.sdd": "auth",
    "src/users/users.sdd": "users",
}


class NativeContractMigrationTests(unittest.TestCase):
    def test_fixture_preserves_durable_native_context(self):
        graph = load_contract_graph(FIXTURE_ROOT)

        auth = resolve_target_context(
            graph,
            "src/auth/service.ts",
        )
        self.assertEqual("auth", auth.owner_id)
        self.assertEqual(("auth",), auth.applicable_contract_ids)
        self.assertEqual(
            ("Auth code must not depend on Users persistence internals.",),
            tuple(item.text for item in auth.prohibitions),
        )
        self.assertEqual(
            ("users",),
            tuple(
                dict.fromkeys(
                    item.contract_id
                    for item in auth.dependency_interfaces
                )
            ),
        )
        self.assertEqual(
            (
                "Consumers use `ExternalIdentityLookup` for external "
                "identity lookup.",
            ),
            tuple(item.text for item in auth.dependency_interfaces),
        )

        users = resolve_target_context(
            graph,
            "src/users/repository.ts",
        )
        self.assertEqual("users", users.owner_id)
        self.assertEqual(("users",), users.applicable_contract_ids)

    def test_native_fixture_resolves_intended_targets_without_provider_state(self):
        graph = load_contract_graph(FIXTURE_ROOT)

        expectations = {
            "src/auth/future-service.ts": "auth",
            "src/users/future-identity-contract.ts": "users",
        }
        for target, expected_owner in expectations.items():
            with self.subTest(target=target):
                context = resolve_target_context(graph, target)
                self.assertEqual(expected_owner, context.owner_id)

    @unittest.skipUnless(
        shutil.which("specdd"),
        "SpecDD CLI is required only for migration parity evidence",
    )
    def test_existing_target_ownership_matches_legacy_adapter_evidence(self):
        targets = (
            "src/auth/service.ts",
            "src/users/identity-contract.ts",
            "src/users/repository.ts",
        )
        legacy = legacy_boundary.build_change_boundary(
            FIXTURE_ROOT,
            targets,
            feature="native-contract-migration",
            schema=legacy_boundary.load_schema(REPO_ROOT),
        )
        self.assertEqual([], legacy["unresolved"])

        graph = load_contract_graph(FIXTURE_ROOT)
        native_owners = {
            target: resolve_target_context(graph, target).owner_id
            for target in targets
        }
        legacy_owners = {
            item["path"]: LEGACY_OWNER_IDS[item["primaryAuthority"]]
            for item in legacy["targets"]
        }

        self.assertEqual(native_owners, legacy_owners)


if __name__ == "__main__":
    unittest.main()
