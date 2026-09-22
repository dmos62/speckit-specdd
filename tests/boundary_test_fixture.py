import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from boundary_test_support import (
    FIXTURE_ROOT,
    REPO_ROOT,
    SCRIPT_PATH,
    boundary,
    validation,
    workflow_gate,
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

    def intended_targets_supported(self):
        return boundary.specdd_resolve_supports_intended_targets(
            FIXTURE_ROOT,
            "specdd",
        )

    def test_two_domain_fixture_produces_valid_cross_boundary(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        targets = (
            "src/users/repository.ts",
            "src/auth/service.ts",
        )
        result = self.run_fixture(*targets)
        rerun = self.run_fixture(*targets)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0, rerun.returncode, rerun.stderr)
        self.assertEqual(result.stdout, rerun.stdout)

        payload = json.loads(result.stdout)
        boundary.validate_boundary(payload, boundary.load_schema(REPO_ROOT))
        self.assertEqual(
            ["src/auth/auth.sdd", "src/users/users.sdd"],
            payload["authorities"],
        )
        self.assertTrue(payload["crossBoundary"])
        self.assertEqual([], payload["unresolved"])
        self.assertEqual(
            ["src/auth/service.ts", "src/users/repository.ts"],
            [target["path"] for target in payload["targets"]],
        )

        rendered = json.dumps(payload, sort_keys=True)
        self.assertIn("1.1.1", rendered)
        self.assertIn("1.5", rendered)

    def test_missing_target_uses_resolver_when_supported(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        result = self.run_fixture("src/auth/missing.ts")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([], payload["targets"])
        self.assertEqual([], payload["authorities"])
        self.assertEqual("UNRESOLVED_TARGET", payload["unresolved"][0]["code"])
        self.assertEqual(
            "src/auth/missing.ts",
            payload["unresolved"][0]["normalizedPath"],
        )

        message = payload["unresolved"][0]["message"]
        if self.intended_targets_supported():
            self.assertNotIn("INTENDED_TARGET_UNSUPPORTED", message)
            self.assertIn("No primary authority", message)
        else:
            self.assertIn("INTENDED_TARGET_UNSUPPORTED", message)
            self.assertIn("SpecDD CLI 1.1.1", message)

    def test_intended_targets_flow_through_permission_and_authorization(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")
        if not self.intended_targets_supported():
            self.skipTest("installed SpecDD CLI lacks intended-target flags")

        feature = "intended-target-fixture"
        targets = (
            "src/auth/future-service.ts",
            "src/users/future-identity-contract.ts",
        )
        fingerprints = {}
        payload = boundary.build_change_boundary(
            FIXTURE_ROOT,
            targets,
            feature=feature,
            schema=boundary.load_schema(REPO_ROOT),
            context_fingerprints=fingerprints,
        )
        self.assertEqual([], payload["unresolved"])
        self.assertEqual(
            ["src/auth/auth.sdd", "src/users/users.sdd"],
            payload["authorities"],
        )

        task = validation.TaskRecord(
            order=0,
            task_id="T001",
            story="US1",
            text="intended cross-owned write",
            targets=targets,
            spec_targets=(),
            invalid_targets=(),
            operation_authority="src/auth/auth.sdd",
        )
        permissions = validation.project_task_modification_permissions(
            FIXTURE_ROOT,
            payload,
            [task],
        )
        result = validation.validate_feature(
            payload,
            [task],
            stage="implementation",
            task_permissions=permissions,
        )
        self.assertEqual(0, result["summary"]["countsBySeverity"]["error"])
        self.assertEqual(0, result["summary"]["countsBySeverity"]["blocking"])
        self.assertEqual(
            ["src/auth/auth.sdd"],
            result["tasks"][0]["operationAuthorities"],
        )
        users_permission = next(
            item
            for item in result["tasks"][0]["modificationPermissions"]
            if item["path"] == "src/users/future-identity-contract.ts"
        )
        self.assertEqual(
            ["src/auth/auth.sdd"],
            users_permission["canModifySources"]["src/auth/auth.sdd"],
        )

        evidence_path = boundary.write_boundary_context_evidence(
            FIXTURE_ROOT,
            payload,
            fingerprints,
        )
        try:
            with tempfile.TemporaryDirectory() as temporary:
                temporary_path = Path(temporary)
                boundary_path = temporary_path / "boundary.json"
                tasks_path = temporary_path / "tasks.md"
                boundary.write_boundary(payload, boundary_path)
                tasks_path.write_text(
                    "- [ ] T001 [US1] Update "
                    "`src/auth/future-service.ts` and "
                    "`src/users/future-identity-contract.ts` "
                    "SPECDD_AUTHORITY: `src/auth/auth.sdd`\n",
                    encoding="utf-8",
                )
                snapshot = temporary_path / "authorization.json"
                spec_plan = temporary_path / "authorization-spec-plan.json"
                stdout = io.StringIO()
                with mock.patch.object(
                    workflow_gate,
                    "write_authorization_evidence",
                    return_value=(snapshot, spec_plan),
                ) as write_evidence:
                    with contextlib.redirect_stdout(stdout):
                        status = workflow_gate._authorize(
                            FIXTURE_ROOT,
                            feature,
                            boundary_path,
                            tasks_path,
                        )
                self.assertEqual(0, status, stdout.getvalue())
                write_evidence.assert_called_once()
        finally:
            evidence_path.unlink(missing_ok=True)
