import shutil
import unittest

from boundary_test_support import (
    FIXTURE_ROOT,
    REPO_ROOT,
    boundary,
    verification,
)


@unittest.skipUnless(
    shutil.which("specdd"),
    "SpecDD CLI is required for the fixture verification test",
)
class RealFixtureVerificationTests(unittest.TestCase):
    def build_boundary(
        self,
        targets,
    ):
        schema = boundary.load_schema(
            REPO_ROOT
        )
        return boundary.build_change_boundary(
            FIXTURE_ROOT,
            targets,
            feature="two-domain-fixture",
            schema=schema,
            cli_version="1.1.1",
            specdd_framework_version="1.5",
        )

    def lint_result(self):
        return {
            "exitCode": 0,
            "stdout": (
                "0 errors, 0 warnings in 5 specs"
            ),
            "stderr": "",
        }

    def test_valid_local_change_verifies(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        planned = self.build_boundary(
            [
                "src/auth/service.ts",
            ]
        )
        actual = self.build_boundary(
            [
                "src/auth/service.ts",
            ]
        )
        changes = verification.ChangeSet(
            writes=(
                verification.GitChange(
                    path="src/auth/service.ts",
                    status="MODIFIED",
                ),
            )
        )

        result = verification.verify_change_set(
            planned,
            actual,
            changes,
            lint=self.lint_result(),
            expected_feature="two-domain-fixture",
        )

        self.assertEqual(
            [],
            result["diagnostics"],
        )
        self.assertFalse(
            result["summary"]["blocking"]
        )

    def test_feature_correct_but_cross_domain_unauthorized_change_blocks(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        planned = self.build_boundary(
            [
                "src/auth/service.ts",
            ]
        )
        actual = self.build_boundary(
            [
                "src/auth/service.ts",
                "src/users/repository.ts",
            ]
        )
        changes = verification.ChangeSet(
            writes=(
                verification.GitChange(
                    path="src/auth/service.ts",
                    status="MODIFIED",
                ),
                verification.GitChange(
                    path="src/users/repository.ts",
                    status="MODIFIED",
                ),
            )
        )

        result = verification.verify_change_set(
            planned,
            actual,
            changes,
            lint=self.lint_result(),
            expected_feature="two-domain-fixture",
        )

        violations = [
            item
            for item in result["diagnostics"]
            if item["code"] == "AUTHORITY_VIOLATION"
        ]
        self.assertEqual(
            1,
            len(violations),
        )
        self.assertEqual(
            ["src/users/repository.ts"],
            violations[0]["targets"],
        )
        self.assertTrue(
            result["summary"]["blocking"]
        )
