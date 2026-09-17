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
    def build_fixture_boundary(self):
        schema = boundary.load_schema(
            REPO_ROOT
        )
        return boundary.build_change_boundary(
            FIXTURE_ROOT,
            [
                "src/auth/service.ts",
                "src/users/repository.ts",
            ],
            feature="two-domain-fixture",
            schema=schema,
            cli_version="1.1.1",
            specdd_framework_version="1.5",
        )

    def test_authority_local_tasks_validate_independently(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

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
            [
                "NORMAL",
                "NORMAL",
            ],
            [
                item["classification"]
                for item in result["tasks"]
            ],
        )
        self.assertEqual(
            [],
            result["diagnostics"],
        )

    def test_combined_cross_domain_task_is_exposed_without_rejection(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T001 [US1] Update src/auth/service.ts and src/users/repository.ts
""",
        )
        result = validation.validate_feature(
            self.build_fixture_boundary(),
            tasks,
            stage="implementation",
            expected_feature="two-domain-fixture",
        )

        self.assertEqual(
            "CROSS_BOUNDARY",
            result["tasks"][0]["classification"],
        )
        self.assertEqual(
            "T001",
            result["tasks"][0]["id"],
        )
        self.assertEqual(
            "US1",
            result["tasks"][0]["story"],
        )
        self.assertEqual(
            ["MULTI_AUTHORITY_TASK"],
            [
                item["code"]
                for item in result["diagnostics"]
            ],
        )
        self.assertFalse(
            result["summary"]["blocking"]
        )

    def test_durable_auth_to_users_contract_is_explicit_spec_evolution(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T003 [US1] SPEC_EVOLUTION_REQUIRED: Extend src/users/users.sdd with a durable Auth-to-Users identity-link contract
""",
        )
        result = validation.validate_feature(
            self.build_fixture_boundary(),
            tasks,
            stage="tasks",
            expected_feature="two-domain-fixture",
        )

        task = result["tasks"][0]
        self.assertEqual(
            "SPEC_EVOLUTION_REQUIRED",
            task["classification"],
        )
        self.assertEqual(
            ["src/users/users.sdd"],
            task["specTargets"],
        )
        self.assertTrue(
            task["evolution"]["requiresFreshBoundary"]
        )
        self.assertFalse(
            task["evolution"]["endsAuthorityContext"]
        )
        self.assertEqual(
            [],
            result["diagnostics"],
        )
