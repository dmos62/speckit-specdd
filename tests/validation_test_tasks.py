import tempfile
import unittest
from pathlib import Path

from boundary_test_support import validation


class ValidationTaskParsingTests(unittest.TestCase):
    def test_preserves_task_identity_and_explicit_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T010 [P] [US1] Update auth and users behavior
  Writes: `src/auth/service.ts`, `src/users/repository.ts`
- [ ] T011 [US2] Update project contract
  Writes: `project.sdd`
""",
            )
        self.assertEqual(2, len(tasks))
        self.assertEqual(0, tasks[0].order)
        self.assertEqual("T010", tasks[0].task_id)
        self.assertEqual("US1", tasks[0].story)
        self.assertEqual(
            (
                "src/auth/service.ts",
                "src/users/repository.ts",
            ),
            tasks[0].targets,
        )
        self.assertTrue(tasks[0].writes_declared)
        self.assertEqual("T011", tasks[1].task_id)
        self.assertEqual("US2", tasks[1].story)
        self.assertEqual((), tasks[1].targets)
        self.assertEqual(("project.sdd",), tasks[1].spec_targets)

    def test_incidental_task_prose_paths_do_not_authorize_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T012 [US1] Update `src/auth/service.ts` and src/users/repository.ts
""",
            )
        self.assertEqual((), tasks[0].targets)
        self.assertEqual((), tasks[0].spec_targets)
        self.assertFalse(tasks[0].writes_declared)

    def test_root_specdd_controls_are_classified_from_writes_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T015 [US1] Update service and project bootstrap override
  Writes: `src/auth/service.ts`, `.specdd/bootstrap.project.md`
""",
            )
        self.assertEqual(
            ("src/auth/service.ts",),
            tasks[0].targets,
        )
        self.assertEqual(
            (".specdd/bootstrap.project.md",),
            tasks[0].control_targets,
        )
        self.assertEqual((), tasks[0].spec_targets)

    def test_backticked_writes_preserve_literal_filename_characters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T014 [US1] Update legacy provider docs
  Writes: `src/auth/provider [legacy].ts`, `docs/guide {draft}.md`
""",
            )
        self.assertEqual(
            (
                "src/auth/provider [legacy].ts",
                "docs/guide {draft}.md",
            ),
            tasks[0].targets,
        )
        self.assertEqual((), tasks[0].invalid_targets)

    def test_invalid_or_duplicate_writes_are_retained_as_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T001 [US1] Update providers
  Writes: `../outside.ts`, `src/auth/*.ts`, `src/auth/service.ts`, `src/auth/service.ts`
  Writes: `src/users/repository.ts`
""",
            )
        self.assertEqual(("src/auth/service.ts",), tasks[0].targets)
        self.assertEqual(
            ("../outside.ts", "src/auth/*.ts"),
            tasks[0].invalid_targets,
        )
        self.assertEqual(
            (
                "duplicate declared write target: src/auth/service.ts",
                "duplicate Writes metadata",
            ),
            tasks[0].write_metadata_errors,
        )
    def test_malformed_writes_metadata_is_not_treated_as_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T001 [US1] Update auth
  Writes: src/auth/service.ts
""",
            )

        self.assertEqual((), tasks[0].targets)
        self.assertEqual(
            ("Writes metadata must use backticked exact paths",),
            tasks[0].write_metadata_errors,
        )

    def test_advisory_path_extraction_remains_available_for_planning(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            targets, specs, invalid = validation.extract_repository_targets(
                root,
                "Use https://example.com/docs/setup, docs/setup.md, and `project.sdd`.",
            )

        self.assertEqual(("docs/setup.md",), targets)
        self.assertEqual(("project.sdd",), specs)
        self.assertEqual((), invalid)

    def test_preserves_explicit_specdd_evolution_classifications(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T020 [US1] SPEC_EVOLUTION_REQUIRED: Extend users contract
  Writes: `src/users/users.sdd`
- [ ] T021 [US1] AUTHORITY_EVOLUTION_REQUIRED: Change repository ownership
  Writes: `src/users/repository.sdd`
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
- [ ] T020 [US1] SPEC_EVOLUTION_REQUIRED: Update users contract
  Writes: `src/users/users.sdd`
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
        self.assertTrue(result["summary"]["freshBoundaryRequiredAfterEvolution"])
        self.assertFalse(result["summary"]["authorityContextEndsAfterEvolution"])
        self.assertEqual([], result["diagnostics"])

    def test_authority_evolution_cannot_mix_implementation_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            tasks = validation.parse_tasks(
                root,
                """
- [ ] T021 [US1] AUTHORITY_EVOLUTION_REQUIRED: Update ownership and repository
  Writes: `src/users/users.sdd`, `src/users/repository.ts`
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
                "authorities": ["src/users/users.sdd"],
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
        self.assertTrue(result["tasks"][0]["evolution"]["endsAuthorityContext"])
        mixed = [
            item
            for item in result["diagnostics"]
            if item["code"] == "EVOLUTION_SCOPE_MIXED"
        ]
        self.assertEqual(1, len(mixed))
        self.assertEqual("blocking", mixed[0]["severity"])
        self.assertTrue(result["summary"]["blocking"])
