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

    def test_scenario_a_owner_local_tasks_validate_independently(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T001 [US1] Update auth service
  Writes: `src/auth/service.ts`
- [ ] T002 [US1] Update users repository
  Writes: `src/users/repository.ts`
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

    def test_coordinated_multi_owner_task_uses_target_owners(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T003 [US1] Coordinate auth and users changes
  Writes: `src/auth/service.ts`, `src/users/repository.ts`
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
            task["authorities"],
        )
        self.assertEqual([], result["diagnostics"])
        self.assertFalse(result["summary"]["blocking"])

    def test_task_prose_path_does_not_enter_implementation_scope(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T004 [US1] Review src/users/repository.ts while updating auth service
  Writes: `src/auth/service.ts`
""",
        )
        result = validation.validate_feature(
            self.build_fixture_boundary(),
            tasks,
            stage="implementation",
            expected_feature="two-domain-fixture",
        )

        self.assertEqual(
            ["src/auth/service.ts"],
            result["tasks"][0]["writeTargets"],
        )
        self.assertEqual(
            ["src/auth/auth.sdd"],
            result["tasks"][0]["authorities"],
        )
        self.assertEqual([], result["diagnostics"])

    def test_durable_contract_is_explicit_spec_evolution(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        tasks = validation.parse_tasks(
            FIXTURE_ROOT,
            """
- [ ] T006 [US1] SPEC_EVOLUTION_REQUIRED: Extend users identity contract
  Writes: `src/users/users.sdd`
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
