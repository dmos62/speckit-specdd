import shutil
import tempfile
import unittest
from pathlib import Path

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
    def build_boundary(self, targets, *, root=FIXTURE_ROOT):
        schema = boundary.load_schema(REPO_ROOT)
        return boundary.build_change_boundary(
            root,
            targets,
            feature="two-domain-fixture",
            schema=schema,
            cli_version="1.1.1",
            specdd_framework_version="1.5",
        )

    def lint_result(self):
        return {
            "exitCode": 0,
            "stdout": "0 errors, 0 warnings in fixture specs",
            "stderr": "",
        }

    def test_valid_local_change_verifies(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        planned = self.build_boundary(["src/auth/service.ts"])
        actual = self.build_boundary(["src/auth/service.ts"])
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

        self.assertEqual([], result["diagnostics"])
        self.assertFalse(result["summary"]["blocking"])

    def test_feature_correct_but_cross_domain_unauthorized_change_blocks(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        planned = self.build_boundary(["src/auth/service.ts"])
        actual = self.build_boundary(
            ["src/auth/service.ts", "src/users/repository.ts"]
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
        self.assertEqual(1, len(violations))
        self.assertEqual(["src/users/repository.ts"], violations[0]["targets"])
        self.assertTrue(result["summary"]["blocking"])

    def test_authority_evolution_requires_a_fresh_boundary(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        with tempfile.TemporaryDirectory(dir=FIXTURE_ROOT.parent) as temporary:
            root = Path(temporary).resolve() / "specdd-two-domain"
            shutil.copytree(FIXTURE_ROOT, root)
            repository_path = "src/users/repository.ts"
            planned = self.build_boundary([repository_path], root=root)

            users_spec = root / "src" / "users" / "users.sdd"
            users_text = users_spec.read_text(encoding="utf-8")
            users_spec.write_text(
                users_text.replace("  ./repository.ts\n", ""),
                encoding="utf-8",
            )
            repository_spec = root / "src" / "users" / "repository.sdd"
            repository_spec.write_text(
                "Spec: Users Repository\n\n"
                "Purpose:\n"
                "  Own Users persistence implementation.\n\n"
                "Owns:\n"
                "  ./repository.ts\n",
                encoding="utf-8",
            )

            evolved = self.build_boundary([repository_path], root=root)

        self.assertEqual(
            ["src/users/users.sdd"],
            planned["authorities"],
        )
        self.assertEqual(
            ["src/users/repository.sdd"],
            evolved["authorities"],
        )

        same_operation = verification.verify_change_set(
            planned,
            evolved,
            verification.ChangeSet(
                writes=(
                    verification.GitChange(
                        path=repository_path,
                        status="MODIFIED",
                    ),
                ),
                specs=(
                    verification.GitChange(
                        path="src/users/users.sdd",
                        status="MODIFIED",
                    ),
                    verification.GitChange(
                        path="src/users/repository.sdd",
                        status="ADDED",
                    ),
                ),
            ),
            lint=self.lint_result(),
            expected_feature="two-domain-fixture",
        )
        self.assertIn(
            "AUTHORITY_VIOLATION",
            [item["code"] for item in same_operation["diagnostics"]],
        )
        self.assertTrue(same_operation["summary"]["blocking"])

        subsequent_operation = verification.verify_change_set(
            evolved,
            evolved,
            verification.ChangeSet(
                writes=(
                    verification.GitChange(
                        path=repository_path,
                        status="MODIFIED",
                    ),
                )
            ),
            lint=self.lint_result(),
            expected_feature="two-domain-fixture",
        )
        self.assertEqual([], subsequent_operation["diagnostics"])
        self.assertFalse(subsequent_operation["summary"]["blocking"])
