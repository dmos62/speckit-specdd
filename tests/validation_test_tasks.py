import tempfile
import unittest
from pathlib import Path

from boundary_test_support import validation


class ValidationTaskParsingTests(unittest.TestCase):
    def test_preserves_task_order_id_story_and_exact_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()

            tasks = validation.parse_tasks(
                root,
                """
- [ ] T010 [P] [US1] Update `src/auth/service.ts` and src/users/repository.ts
- [ ] T011 [US2] Update `project.sdd`
""",
            )

        self.assertEqual(
            2,
            len(tasks),
        )
        self.assertEqual(
            0,
            tasks[0].order,
        )
        self.assertEqual(
            "T010",
            tasks[0].task_id,
        )
        self.assertEqual(
            "US1",
            tasks[0].story,
        )
        self.assertEqual(
            (
                "src/auth/service.ts",
                "src/users/repository.ts",
            ),
            tasks[0].targets,
        )
        self.assertEqual(
            (),
            tasks[0].spec_targets,
        )

        self.assertEqual(
            "T011",
            tasks[1].task_id,
        )
        self.assertEqual(
            "US2",
            tasks[1].story,
        )
        self.assertEqual(
            (),
            tasks[1].targets,
        )
        self.assertEqual(
            ("project.sdd",),
            tasks[1].spec_targets,
        )

    def test_invalid_or_glob_targets_are_kept_out_of_write_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()

            tasks = validation.parse_tasks(
                root,
                """
- [ ] T001 [US1] Update `../outside.ts` and `src/auth/*.ts`
""",
            )

        self.assertEqual(
            (),
            tasks[0].targets,
        )
        self.assertEqual(
            (
                "../outside.ts",
                "src/auth/*.ts",
            ),
            tasks[0].invalid_targets,
        )

    def test_ignores_urls_as_repository_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()

            tasks = validation.parse_tasks(
                root,
                """
- [ ] T001 Document https://example.com/docs/setup and docs/setup.md
""",
            )

        self.assertEqual(
            ("docs/setup.md",),
            tasks[0].targets,
        )
