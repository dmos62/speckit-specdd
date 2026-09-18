import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from boundary_test_support import verification, workflow_gate


class WorkflowPermissionAuthorizationTests(unittest.TestCase):
    def initialize_operation(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name).resolve()
        subprocess.run(
            ["git", "init", "-q"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        feature_dir = root / "specs" / "001-login"
        boundary_path = feature_dir / ".specdd" / "boundary.json"
        task_path = feature_dir / "tasks.md"
        boundary_path.parent.mkdir(parents=True)
        boundary = {
            "schemaVersion": 1,
            "feature": "001-login",
            "targets": [
                {
                    "path": "src/auth/service.ts",
                    "primaryAuthority": "src/auth/auth.sdd",
                    "resolvedSpecs": ["src/auth/auth.sdd"],
                },
                {
                    "path": "src/users/identity-contract.ts",
                    "primaryAuthority": "src/users/users.sdd",
                    "resolvedSpecs": ["src/users/users.sdd"],
                },
            ],
            "authorities": [
                "src/auth/auth.sdd",
                "src/users/users.sdd",
            ],
            "crossBoundary": True,
            "unresolved": [],
            "generation": {
                "specddCliVersion": "1.1.1",
                "specddFrameworkVersion": "1.5",
            },
        }
        boundary_path.write_text(json.dumps(boundary), encoding="utf-8")
        task_path.write_text(
            "- [ ] T001 [US1] SPECDD_AUTHORITY: `src/auth/auth.sdd` "
            "Update src/auth/service.ts and src/users/identity-contract.ts\n",
            encoding="utf-8",
        )
        return temporary, root, boundary, boundary_path, task_path

    def permissions(self, *, permit):
        auth = "src/auth/auth.sdd"
        users = "src/users/users.sdd"
        return {
            0: {
                "src/auth/service.ts": {
                    "owner": auth,
                    "allowedAuthorities": [auth],
                    "canModifySources": {},
                },
                "src/users/identity-contract.ts": {
                    "owner": users,
                    "allowedAuthorities": [auth, users] if permit else [users],
                    "canModifySources": {auth: [auth]} if permit else {},
                },
            }
        }

    def evidence(self, root):
        snapshot = verification.authorization_snapshot_path(root)
        stored = json.loads(snapshot.read_text(encoding="utf-8"))
        plan = verification.authorization_spec_plan_path(root)
        specs, controls = verification.load_authorization_plan(
            root,
            plan,
            stored,
        )
        return stored, specs, controls

    def test_authorization_accepts_explicit_cross_owned_permission(self):
        temporary, root, boundary, boundary_path, task_path = (
            self.initialize_operation()
        )
        with (
            temporary,
            mock.patch.object(
                workflow_gate,
                "project_task_modification_permissions",
                return_value=self.permissions(permit=True),
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            status = workflow_gate._authorize(
                root,
                "001-login",
                boundary_path,
                task_path,
            )
            stored, planned_specs, planned_controls = self.evidence(root)

        self.assertEqual(0, status)
        self.assertEqual(boundary, stored)
        self.assertEqual((), planned_specs)
        self.assertEqual({}, planned_controls)

    def test_authorization_records_explicit_spec_evolution_targets(self):
        temporary, root, _, boundary_path, task_path = self.initialize_operation()
        task_path.write_text(
            "- [ ] T000 [US1] SPEC_EVOLUTION_REQUIRED: "
            "Update `src/auth/auth.sdd`\n"
            "- [ ] T001 [US1] Update src/auth/service.ts\n",
            encoding="utf-8",
        )
        with temporary, contextlib.redirect_stdout(io.StringIO()):
            status = workflow_gate._authorize(
                root,
                "001-login",
                boundary_path,
                task_path,
            )
            _, planned_specs, planned_controls = self.evidence(root)

        self.assertEqual(0, status)
        self.assertEqual(("src/auth/auth.sdd",), planned_specs)
        self.assertEqual({}, planned_controls)

    def test_authorization_records_workflow_selected_project_override(self):
        temporary, root, _, boundary_path, task_path = self.initialize_operation()
        task_path.write_text(
            "- [ ] T001 [US1] Update src/auth/service.ts and "
            "`.specdd/bootstrap.project.md`\n",
            encoding="utf-8",
        )
        with temporary, contextlib.redirect_stdout(io.StringIO()):
            status = workflow_gate._authorize(
                root,
                "001-login",
                boundary_path,
                task_path,
            )
            _, _, controls = self.evidence(root)

        self.assertEqual(0, status)
        self.assertEqual(
            {".specdd/bootstrap.project.md": "workflow"},
            controls,
        )

    def test_authorization_records_operator_selected_project_override(self):
        temporary, root, _, boundary_path, task_path = self.initialize_operation()
        with (
            temporary,
            mock.patch.object(
                workflow_gate,
                "project_task_modification_permissions",
                return_value=self.permissions(permit=True),
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            status = workflow_gate._authorize(
                root,
                "001-login",
                boundary_path,
                task_path,
                operator_controls=(".specdd/bootstrap.project.md",),
            )
            _, _, controls = self.evidence(root)

        self.assertEqual(0, status)
        self.assertEqual(
            {".specdd/bootstrap.project.md": "operator"},
            controls,
        )

    def test_authorization_rejects_immutable_bootstrap_selection(self):
        temporary, root, _, boundary_path, task_path = self.initialize_operation()
        task_path.write_text(
            "- [ ] T001 [US1] Update src/auth/service.ts and "
            "`.specdd/bootstrap.md`\n",
            encoding="utf-8",
        )
        with temporary, contextlib.redirect_stdout(io.StringIO()):
            status = workflow_gate._authorize(
                root,
                "001-login",
                boundary_path,
                task_path,
            )
            snapshot_exists = verification.authorization_snapshot_path(root).exists()
            plan_exists = verification.authorization_spec_plan_path(root).exists()

        self.assertEqual(1, status)
        self.assertFalse(snapshot_exists)
        self.assertFalse(plan_exists)

    def test_authorization_rejects_cross_owned_write_without_permission(self):
        temporary, root, _, boundary_path, task_path = self.initialize_operation()
        with (
            temporary,
            mock.patch.object(
                workflow_gate,
                "project_task_modification_permissions",
                return_value=self.permissions(permit=False),
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            status = workflow_gate._authorize(
                root,
                "001-login",
                boundary_path,
                task_path,
            )
            snapshot_exists = verification.authorization_snapshot_path(root).exists()
            plan_exists = verification.authorization_spec_plan_path(root).exists()

        self.assertEqual(1, status)
        self.assertFalse(snapshot_exists)
        self.assertFalse(plan_exists)
