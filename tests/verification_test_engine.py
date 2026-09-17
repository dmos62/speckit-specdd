import unittest

from boundary_test_support import verification


def boundary(
    *,
    targets,
    authorities,
):
    return {
        "schemaVersion": 1,
        "feature": "001-login",
        "targets": targets,
        "authorities": authorities,
        "crossBoundary": len(authorities) > 1,
        "unresolved": [],
        "generation": {
            "specddCliVersion": "1.1.1",
            "specddFrameworkVersion": "1.5",
        },
    }


def target(
    path,
    authority,
):
    return {
        "path": path,
        "primaryAuthority": authority,
        "resolvedSpecs": [
            "project.sdd",
            authority,
        ],
    }


def changes(
    *paths,
    specs=(),
):
    return verification.ChangeSet(
        writes=tuple(
            verification.GitChange(
                path=path,
                status="MODIFIED",
            )
            for path in paths
        ),
        specs=tuple(
            verification.GitChange(
                path=path,
                status="MODIFIED",
            )
            for path in specs
        ),
    )


def lint(
    exit_code=0,
):
    return {
        "exitCode": exit_code,
        "stdout": "",
        "stderr": "",
    }


class VerificationEngineTests(unittest.TestCase):
    def setUp(self):
        self.auth = "src/auth/auth.sdd"
        self.users = "src/users/users.sdd"
        self.auth_path = "src/auth/service.ts"
        self.users_path = "src/users/repository.ts"

    def test_valid_local_actual_change_has_no_findings(self):
        planned = boundary(
            targets=[
                target(
                    self.auth_path,
                    self.auth,
                )
            ],
            authorities=[self.auth],
        )
        actual = boundary(
            targets=[
                target(
                    self.auth_path,
                    self.auth,
                )
            ],
            authorities=[self.auth],
        )

        result = verification.verify_change_set(
            planned,
            actual,
            changes(
                self.auth_path,
            ),
            lint=lint(),
            expected_feature="001-login",
        )

        self.assertEqual(
            [],
            result["diagnostics"],
        )
        self.assertFalse(
            result["summary"]["blocking"]
        )

    def test_unplanned_target_in_same_authority_reports_drift(self):
        new_path = "src/auth/provider.ts"
        planned = boundary(
            targets=[
                target(
                    self.auth_path,
                    self.auth,
                )
            ],
            authorities=[self.auth],
        )
        actual = boundary(
            targets=[
                target(
                    new_path,
                    self.auth,
                )
            ],
            authorities=[self.auth],
        )

        result = verification.verify_change_set(
            planned,
            actual,
            changes(
                new_path,
            ),
            lint=lint(),
        )

        self.assertEqual(
            ["SPECDD_DRIFT"],
            [
                item["code"]
                for item in result["diagnostics"]
            ],
        )
        self.assertFalse(
            result["summary"]["blocking"]
        )

    def test_new_actual_authority_is_blocking(self):
        planned = boundary(
            targets=[
                target(
                    self.auth_path,
                    self.auth,
                )
            ],
            authorities=[self.auth],
        )
        actual = boundary(
            targets=[
                target(
                    self.auth_path,
                    self.auth,
                ),
                target(
                    self.users_path,
                    self.users,
                ),
            ],
            authorities=[
                self.auth,
                self.users,
            ],
        )

        result = verification.verify_change_set(
            planned,
            actual,
            changes(
                self.auth_path,
                self.users_path,
            ),
            lint=lint(),
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
            [self.users_path],
            violations[0]["targets"],
        )
        self.assertTrue(
            result["summary"]["blocking"]
        )

    def test_spec_change_does_not_authorize_new_domain(self):
        planned = boundary(
            targets=[
                target(
                    self.auth_path,
                    self.auth,
                )
            ],
            authorities=[self.auth],
        )
        actual = boundary(
            targets=[
                target(
                    self.users_path,
                    self.users,
                )
            ],
            authorities=[self.users],
        )

        result = verification.verify_change_set(
            planned,
            actual,
            changes(
                self.users_path,
                specs=("src/auth/auth.sdd",),
            ),
            lint=lint(),
        )

        codes = [
            item["code"]
            for item in result["diagnostics"]
        ]
        self.assertIn(
            "SPEC_EVOLUTION_PRESENT",
            codes,
        )
        self.assertIn(
            "AUTHORITY_VIOLATION",
            codes,
        )
        self.assertTrue(
            result["summary"]["blocking"]
        )

    def test_unplanned_deleted_target_is_blocking(self):
        planned = boundary(
            targets=[],
            authorities=[],
        )
        actual = boundary(
            targets=[],
            authorities=[],
        )
        deleted = verification.ChangeSet(
            writes=(
                verification.GitChange(
                    path=self.users_path,
                    status="DELETED",
                    deleted=True,
                ),
            )
        )

        result = verification.verify_change_set(
            planned,
            actual,
            deleted,
            lint=lint(),
        )

        self.assertEqual(
            "AUTHORITY_VIOLATION",
            result["diagnostics"][0]["code"],
        )
        self.assertTrue(
            result["summary"]["blocking"]
        )

    def test_specdd_lint_failure_is_blocking_system_violation(self):
        planned = boundary(
            targets=[],
            authorities=[],
        )
        actual = boundary(
            targets=[],
            authorities=[],
        )

        result = verification.verify_change_set(
            planned,
            actual,
            verification.ChangeSet(),
            lint=lint(1),
        )

        self.assertEqual(
            "SPECDD_VIOLATION",
            result["diagnostics"][0]["code"],
        )
        self.assertTrue(
            result["summary"]["blocking"]
        )
