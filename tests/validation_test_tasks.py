import tempfile
import unittest
from pathlib import Path

from boundary_test_support import validation


class ValidationTaskParsingTests(unittest.TestCase):
    def test_preserves_task_order_id_story_and_exact_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
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

    def test_operation_authority_annotation_is_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T012 [US1] SPECDD_AUTHORITY: `src/auth/auth.sdd` Update `src/users/identity-contract.ts`
""",
            )

        self.assertEqual(
            "src/auth/auth.sdd",
            tasks[0].operation_authority,
        )
        self.assertEqual(
            ("src/users/identity-contract.ts",),
            tasks[0].targets,
        )
        self.assertEqual(
            (),
            tasks[0].spec_targets,
        )
        self.assertEqual(
            (),
            tasks[0].invalid_operation_authorities,
        )

    def test_conflicting_operation_authorities_are_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T013 [US1] SPECDD_AUTHORITY: `src/auth/auth.sdd` SPECDD_AUTHORITY: `src/users/users.sdd` Update `src/users/identity-contract.ts`
""",
            )

        self.assertIsNone(
            tasks[0].operation_authority
        )
        self.assertEqual(
            (
                "src/auth/auth.sdd",
                "src/users/users.sdd",
            ),
            tasks[0].invalid_operation_authorities,
        )
        self.assertEqual(
            (),
            tasks[0].spec_targets,
        )

    def test_backticked_paths_preserve_literal_filename_characters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T014 [US1] Update `src/auth/provider [legacy].ts` and `docs/guide {draft}.md`
""",
            )

        self.assertEqual(
            (
                "src/auth/provider [legacy].ts",
                "docs/guide {draft}.md",
            ),
            tasks[0].targets,
        )
        self.assertEqual(
            (),
            tasks[0].invalid_targets,
        )

    def test_invalid_patterns_are_kept_out_of_write_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
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

    def test_unquoted_grouping_syntax_is_not_an_exact_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T001 [US1] Update src/auth/provider[legacy].ts
""",
            )

        self.assertEqual(
            (),
            tasks[0].targets,
        )
        self.assertEqual(
            ("src/auth/provider[legacy].ts",),
            tasks[0].invalid_targets,
        )

    def test_ignores_urls_as_repository_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
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

    def test_preserves_explicit_specdd_evolution_classifications(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T020 [US1] SPEC_EVOLUTION_REQUIRED: Update `src/users/users.sdd`
- [ ] T021 [US1] AUTHORITY_EVOLUTION_REQUIRED: Update `src/users/repository.sdd`
""",
            )

        self.assertEqual(
            ("SPEC_EVOLUTION_REQUIRED",),
            tasks[0].evolution_markers,
        )
        self.assertEqual(
            ("AUTHORITY_EVOLUTION_REQUIRED",),
            tasks[1].evolution_markers,
        )

    def test_spec_evolution_projects_fresh_boundary_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T020 [US1] SPEC_EVOLUTION_REQUIRED: Update `src/users/users.sdd`
""",
            )

        result = validation.validate_feature(
            {
                "feature": "001-login",
                "targets": [],
                "authorities": [],
                "crossBoundary": False,
                "unresolved": [],
            },
            tasks,
            stage="tasks",
            expected_feature="001-login",
        )

        task = result["tasks"][0]
        self.assertEqual(
            "SPEC_EVOLUTION_REQUIRED",
            task["classification"],
        )
        self.assertEqual(
            {
                "classification": "SPEC_EVOLUTION_REQUIRED",
                "specTargets": ["src/users/users.sdd"],
                "requiresFreshBoundary": True,
                "endsAuthorityContext": False,
            },
            task["evolution"],
        )
        self.assertTrue(
            result["summary"][
                "freshBoundaryRequiredAfterEvolution"
            ]
        )
        self.assertFalse(
            result["summary"][
                "authorityContextEndsAfterEvolution"
            ]
        )
        self.assertEqual(
            [],
            result["diagnostics"],
        )

    def test_authority_evolution_cannot_mix_implementation_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T021 [US1] AUTHORITY_EVOLUTION_REQUIRED: Update `src/users/users.sdd` and `src/users/repository.ts`
""",
            )

        result = validation.validate_feature(
            {
                "feature": "001-login",
                "targets": [
                    {
                        "path": "src/users/repository.ts",
                        "primaryAuthority": "src/users/users.sdd",
                    }
                ],
                "authorities": [
                    "src/users/users.sdd"
                ],
                "crossBoundary": False,
                "unresolved": [],
            },
            tasks,
            stage="implementation",
            expected_feature="001-login",
        )

        self.assertEqual(
            "AUTHORITY_EVOLUTION_REQUIRED",
            result["tasks"][0]["classification"],
        )
        self.assertTrue(
            result["tasks"][0]["evolution"][
                "endsAuthorityContext"
            ]
        )
        mixed = [
            item
            for item in result["diagnostics"]
            if item["code"] == "EVOLUTION_SCOPE_MIXED"
        ]
        self.assertEqual(
            1,
            len(mixed),
        )
        self.assertEqual(
            "blocking",
            mixed[0]["severity"],
        )
        self.assertTrue(
            result["summary"]["blocking"]
        )
