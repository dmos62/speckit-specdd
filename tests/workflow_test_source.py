import unittest

from preset_test_support import (
    INSTALLER_PATH,
    INSTALLED_RUNTIME_PATH,
    WORKFLOW_OVERLAY_PATH,
)


class WorkflowSourceTests(unittest.TestCase):
    def test_overlay_places_only_authorization_and_verification_gates(self):
        content = WORKFLOW_OVERLAY_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'id: "specdd-bridge"',
            content,
        )
        self.assertIn(
            'extends: "speckit"',
            content,
        )
        self.assertEqual(
            2,
            content.count("type: shell"),
        )
        self.assertNotIn(
            "continue_on_error",
            content,
        )

        expected = (
            (
                "insert_before: implement",
                "boundary-authorize",
                "authorize",
            ),
            (
                "insert_after: implement",
                "boundary-verify",
                "verify",
            ),
        )
        for anchor, step, stage in expected:
            with self.subTest(step=step):
                self.assertIn(anchor, content)
                self.assertIn(f"id: {step}", content)
                self.assertIn(
                    (
                        "uv run --no-project python "
                        f"{INSTALLED_RUNTIME_PATH.as_posix()} {stage}"
                    ),
                    content,
                )

        for obsolete in (
            "insert_after: plan",
            "insert_after: tasks",
            "specdd-context",
            "specdd-task-validation",
            "workflow_gate.py context",
            "workflow_gate.py tasks",
        ):
            self.assertNotIn(obsolete, content)

        self.assertEqual(
            2,
            content.count("required command not found: uv"),
        )
        self.assertEqual(
            2,
            content.count("exit 2"),
        )
        self.assertNotIn(
            "integration/specdd/scripts/adapter_gate.py",
            content,
        )
        self.assertNotIn(
            "bash scripts/bootstrap.sh --check",
            content,
        )

    def test_installer_manages_overlay_through_spec_kit(self):
        content = INSTALLER_PATH.read_text(
            encoding="utf-8"
        )

        for marker in (
            "specify workflow overlay add",
            "specify workflow overlay remove",
            "specify workflow resolve",
        ):
            self.assertIn(marker, content)

        self.assertNotIn(
            "cp integration/specdd/workflow-overlay.yml .specify",
            content,
        )
