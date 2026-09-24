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
        self.assertEqual(
            "1.2.0",
            payload["generation"]["specddCliVersion"],
        )
        self.assertEqual(
            "not-required",
            payload["generation"]["specddFrameworkVersion"],
        )

    def test_missing_target_uses_resolver_when_supported(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest("two-domain fixture is not available")

        result = self.run_fixture("src/auth/missing.ts")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([], payload["targets"])
        self.assertEqual([], payload["authorities"])
        self.assertEqual(
            "src/auth/missing.ts",
            payload["unresolved"][0]["normalizedPath"],
        )

        supported = self.intended_targets_supported()
        record = payload["unresolved"][0]
        message = record["message"]
        if supported:
            self.assertEqual("UNRESOLVED_TARGET", record["code"])
            self.assertNotIn("INTENDED_TARGET_UNSUPPORTED", message)
            self.assertIn("No primary authority", message)
        else:
            self.assertEqual(
                "INTENDED_TARGET_UNSUPPORTED",
                record["code"],
            )
            self.assertNotIn("INTENDED_TARGET_UNSUPPORTED", message)
            self.assertIn(
                f"SpecDD CLI {boundary.specdd_cli_version(FIXTURE_ROOT, 'specdd')}",
                message,
            )

    def test_intended_targets_flow_through_explicit_writes_and_authorization(self):
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

        task_text = (
            "- [ ] T001 [US1] Implement intended cross-owner write\n"
            "  Writes: `src/auth/future-service.ts`, "
            "`src/users/future-identity-contract.ts`\n"
        )
        tasks = validation.parse_tasks(FIXTURE_ROOT, task_text)
        result = validation.validate_feature(
            payload,
            tasks,
            stage="implementation",
        )
        self.assertEqual(0, result["summary"]["countsBySeverity"]["error"])
        self.assertEqual(0, result["summary"]["countsBySeverity"]["blocking"])
        self.assertEqual(
            ["src/auth/auth.sdd", "src/users/users.sdd"],
            result["tasks"][0]["authorities"],
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
                tasks_path.write_text(task_text, encoding="utf-8")
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
