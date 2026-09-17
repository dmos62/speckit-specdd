import json
import shutil
import subprocess
import sys
import unittest

from boundary_test_support import (
    FIXTURE_ROOT,
    REPO_ROOT,
    SCRIPT_PATH,
    boundary,
)


@unittest.skipUnless(
    shutil.which("specdd"),
    "SpecDD CLI is required for the fixture integration test",
)
class RealFixtureIntegrationTests(unittest.TestCase):
    def run_fixture(self, *targets):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--root",
                str(FIXTURE_ROOT),
                "--feature",
                "two-domain-fixture",
                *targets,
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_two_domain_fixture_produces_valid_cross_boundary(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        targets = (
            "src/users/repository.ts",
            "src/auth/service.ts",
        )
        result = self.run_fixture(*targets)
        rerun = self.run_fixture(*targets)

        self.assertEqual(
            0,
            result.returncode,
            result.stderr,
        )
        self.assertEqual(
            0,
            rerun.returncode,
            rerun.stderr,
        )
        self.assertEqual(
            result.stdout,
            rerun.stdout,
        )

        payload = json.loads(
            result.stdout
        )
        schema = boundary.load_schema(
            REPO_ROOT
        )
        boundary.validate_boundary(
            payload,
            schema,
        )

        self.assertEqual(
            [
                "src/auth/auth.sdd",
                "src/users/users.sdd",
            ],
            payload["authorities"],
        )
        self.assertTrue(
            payload["crossBoundary"]
        )
        self.assertEqual(
            [],
            payload["unresolved"],
        )
        self.assertEqual(
            [
                "src/auth/service.ts",
                "src/users/repository.ts",
            ],
            [
                target["path"]
                for target in payload["targets"]
            ],
        )

        rendered = json.dumps(
            payload,
            sort_keys=True,
        )
        self.assertIn(
            "1.1.1",
            rendered,
        )
        self.assertIn(
            "1.5",
            rendered,
        )

    def test_missing_target_is_preserved_as_unresolved(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        result = self.run_fixture(
            "src/auth/missing.ts"
        )
        self.assertEqual(
            0,
            result.returncode,
            result.stderr,
        )

        payload = json.loads(
            result.stdout
        )
        self.assertEqual(
            [],
            payload["targets"],
        )
        self.assertEqual(
            [],
            payload["authorities"],
        )
        self.assertEqual(
            "UNRESOLVED_TARGET",
            payload["unresolved"][0]["code"],
        )
        self.assertEqual(
            "src/auth/missing.ts",
            payload["unresolved"][0]["normalizedPath"],
        )

    def test_real_resolver_failure_is_normalized(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        target = boundary.normalize_target(
            FIXTURE_ROOT,
            "src/auth/missing.ts",
        )
        specs, error = boundary.resolve_target(
            FIXTURE_ROOT,
            target,
            "specdd",
        )

        self.assertIsNone(specs)
        self.assertIsNotNone(error)
        self.assertRegex(
            error,
            r"^SpecDD resolve exited with status [1-9][0-9]*",
        )
