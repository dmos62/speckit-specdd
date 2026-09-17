import unittest

from preset_test_support import (
    BOOTSTRAP_PATH,
    WORKFLOW_OVERLAY_PATH,
)


class WorkflowSourceTests(unittest.TestCase):
    def test_overlay_places_four_structural_shell_gates(self):
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
            ("insert_after: plan", "id: specdd-context"),
            (
                "insert_after: tasks",
                "id: specdd-task-validation",
            ),
            (
                "insert_before: implement",
                "id: specdd-authorize",
            ),
            (
                "insert_after: implement",
                "id: specdd-verify",
            ),
        )
        for anchor, step in expected:
            with self.subTest(step=step):
                self.assertIn(
                    anchor,
                    content,
                )
                self.assertIn(
                    step,
                    content,
                )

    def test_overlay_invokes_deterministic_workflow_gate(self):
        content = WORKFLOW_OVERLAY_PATH.read_text(
            encoding="utf-8"
        )

        for stage in (
            "context",
            "tasks",
            "authorize",
            "verify",
        ):
            self.assertIn(
                (
                    "uv run --no-project python "
                    "integration/specdd/scripts/workflow_gate.py "
                    f"{stage}"
                ),
                content,
            )

    def test_bootstrap_installs_overlay_through_spec_kit(self):
        content = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "specify workflow overlay add",
            content,
        )
        self.assertIn(
            "specify workflow overlay remove",
            content,
        )
        self.assertIn(
            "specify workflow resolve speckit",
            content,
        )
        self.assertNotIn(
            "cp integration/specdd/workflow-overlay.yml .specify",
            content,
        )
