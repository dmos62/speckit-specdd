import unittest

from preset_test_support import (
    INSTALLER_PATH,
    INSTALLED_RUNTIME_PATH,
    WORKFLOW_OVERLAY_PATH,
)


class WorkflowSourceTests(unittest.TestCase):
    def test_overlay_places_four_fail_closed_structural_gates(self):
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
            4,
            content.count("type: shell"),
        )
        self.assertNotIn(
            "continue_on_error",
            content,
        )

        expected = (
            ("insert_after: plan", "specdd-context", "context"),
            ("insert_after: tasks", "specdd-task-validation", "tasks"),
            ("insert_before: implement", "specdd-authorize", "authorize"),
            ("insert_after: implement", "specdd-verify", "verify"),
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

        self.assertEqual(
            4,
            content.count("required command not found: uv"),
        )
        self.assertEqual(
            4,
            content.count("exit 2"),
        )
        self.assertNotIn(
            "integration/specdd/scripts/workflow_gate.py",
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
