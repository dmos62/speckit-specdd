import shutil
import unittest

from boundary_test_support import (
    FIXTURE_ROOT,
    REPO_ROOT,
    boundary,
    validation,
)


@unittest.skipUnless(
    shutil.which("specdd"),
    "SpecDD CLI is required for the fixture validation test",
)
class RealFixtureValidationTests(unittest.TestCase):
    def build_fixture_boundary(self, targets=None):
        schema = boundary.load_schema(REPO_ROOT)
        return boundary.build_change_boundary(
            FIXTURE_ROOT,
            targets
            or [
                "src/auth/service.ts",
                "src/users/repository.ts",
            ],
            feature="two-domain-fixture",
            schema=schema,
            cli_version="1.1.1",
            specdd_framework_version="1.5",
        )

    def permission_projection(self, boundary_value, tasks):
        return validation.project_task_modification_permissions(
            FIXTURE_ROOT,
            boundary_value,
            tasks,
        )

    def test_scenario_a_authority_local_tasks_validate_independently(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T001 [US1] Update src/auth/service.ts
- [ ] T002 [US1] Update src/users/repository.ts
""",
        )
        result = validation.validate_feature(
            self.build_fixture_boundary(),
            tasks,
            stage="tasks",
            expected_feature="two-domain-fixture",
        )

        self.assertEqual(
            ["NORMAL", "NORMAL"],
            [item["classification"] for item in result["tasks"]],
        )
        self.assertEqual([], result["diagnostics"])

    def test_scenario_c_unmarked_cross_domain_task_remains_representable(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T003 [US1] Update src/auth/service.ts and src/users/repository.ts
""",
        )
        result = validation.validate_feature(
            self.build_fixture_boundary(),
            tasks,
            stage="implementation",
            expected_feature="two-domain-fixture",
        )

        task = result["tasks"][0]
        self.assertEqual("CROSS_BOUNDARY", task["classification"])
        self.assertEqual(
            ["src/auth/auth.sdd", "src/users/users.sdd"],
            task["operationAuthorities"],
        )
        self.assertEqual(
            ["MULTI_AUTHORITY_TASK"],
            [item["code"] for item in result["diagnostics"]],
        )
        self.assertFalse(result["summary"]["blocking"])

    def test_declared_auth_write_to_users_contract_uses_can_modify(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T004 [US1] SPECDD_AUTHORITY: `src/auth/auth.sdd` Update src/auth/service.ts and src/users/identity-contract.ts
""",
        )
        boundary_value = self.build_fixture_boundary(
            [
                "src/auth/service.ts",
                "src/users/identity-contract.ts",
            ]
        )
        result = validation.validate_feature(
            boundary_value,
            tasks,
            stage="implementation",
            expected_feature="two-domain-fixture",
            task_permissions=self.permission_projection(boundary_value, tasks),
        )

        task = result["tasks"][0]
        self.assertEqual(
            ["src/auth/auth.sdd"],
            task["operationAuthorities"],
        )
        identity_permission = next(
            item
            for item in task["modificationPermissions"]
            if item["path"] == "src/users/identity-contract.ts"
        )
        self.assertEqual("src/users/users.sdd", identity_permission["owner"])
        self.assertEqual(
            ["src/auth/auth.sdd"],
            identity_permission["canModifySources"]["src/auth/auth.sdd"],
        )
        self.assertEqual(
            ["MULTI_AUTHORITY_TASK"],
            [item["code"] for item in result["diagnostics"]],
        )
        self.assertFalse(result["summary"]["blocking"])

    def test_declared_auth_write_to_users_repository_without_grant_is_blocked(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T005 [US1] SPECDD_AUTHORITY: `src/auth/auth.sdd` Update src/auth/service.ts and src/users/repository.ts
""",
        )
        boundary_value = self.build_fixture_boundary()
        result = validation.validate_feature(
            boundary_value,
            tasks,
            stage="implementation",
            expected_feature="two-domain-fixture",
            task_permissions=self.permission_projection(boundary_value, tasks),
        )

        self.assertEqual([], result["tasks"][0]["operationAuthorities"])
        self.assertIn(
            "AUTHORITY_VIOLATION",
            [item["code"] for item in result["diagnostics"]],
        )
        self.assertTrue(result["summary"]["blocking"])

    def test_scenario_d_durable_contract_is_explicit_spec_evolution(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T006 [US1] SPEC_EVOLUTION_REQUIRED: Extend src/users/users.sdd with a durable Auth-to-Users identity-link contract
""",
        )
        result = validation.validate_feature(
            self.build_fixture_boundary(),
            tasks,
            stage="tasks",
            expected_feature="two-domain-fixture",
        )

        task = result["tasks"][0]
        self.assertEqual("SPEC_EVOLUTION_REQUIRED", task["classification"])
        self.assertEqual(["src/users/users.sdd"], task["specTargets"])
        self.assertTrue(task["evolution"]["requiresFreshBoundary"])
        self.assertFalse(task["evolution"]["endsAuthorityContext"])
        self.assertEqual([], result["diagnostics"])
