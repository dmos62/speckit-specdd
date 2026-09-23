import unittest

from boundary.authorization import ChangeWriteSet, TaskWriteSet, WriteSetError


class AuthorizationWriteSetTests(unittest.TestCase):
    def test_preserves_task_identity_order_and_exact_writes(self):
        first = TaskWriteSet(
            order=0,
            task_id="T010",
            story="US1",
            writes=("src/auth/service.ts", "src/users/repository.ts"),
        )
        second = TaskWriteSet(
            order=1,
            task_id="T011",
            story="US2",
            writes=("src/auth/service.ts", "docs/login.md"),
        )
        change = ChangeWriteSet(
            change_id="001-login",
            tasks=(first, second),
        )

        self.assertEqual((0, 1), tuple(task.order for task in change.tasks))
        self.assertEqual(("T010", "T011"), tuple(task.task_id for task in change.tasks))
        self.assertEqual(("US1", "US2"), tuple(task.story for task in change.tasks))
        self.assertEqual(
            (
                "src/auth/service.ts",
                "src/users/repository.ts",
                "docs/login.md",
            ),
            change.writes,
        )

    def test_rejects_noncanonical_or_duplicate_writes(self):
        with self.assertRaisesRegex(WriteSetError, "canonical repository syntax"):
            TaskWriteSet(
                order=0,
                task_id="T001",
                story="US1",
                writes=("src/auth/./service.ts",),
            )
        with self.assertRaisesRegex(WriteSetError, "duplicated"):
            TaskWriteSet(
                order=0,
                task_id="T001",
                story="US1",
                writes=("src/auth/service.ts", "src/auth/service.ts"),
            )

    def test_change_write_set_requires_canonical_task_order(self):
        later = TaskWriteSet(1, "T002", "US1", ("src/b.ts",))
        earlier = TaskWriteSet(0, "T001", "US1", ("src/a.ts",))
        with self.assertRaisesRegex(WriteSetError, "canonical task order"):
            ChangeWriteSet("001-change", (later, earlier))


if __name__ == "__main__":
    unittest.main()
