import unittest

from boundary_test_support import validation
from validation_test_support import sample_boundary, task


class ValidationEngineTests(unittest.TestCase):
    def test_single_authority_task_is_normal(self):
        result = validation.validate_feature(
            sample_boundary(),
            [task(targets=["src/auth/service.ts"])],
            stage="tasks",
            expected_feature="001-login",
        )
        self.assertEqual("NORMAL", result["tasks"][0]["classification"])
        self.assertEqual(
            ["src/auth/auth.sdd"],
            result["tasks"][0]["authorities"],
        )
        self.assertTrue(result["tasks"][0]["writesDeclared"])
        self.assertFalse(result["summary"]["blocking"])
        self.assertEqual([], result["diagnostics"])

    def test_multi_authority_task_uses_each_target_owner_directly(self):
        result = validation.validate_feature(
            sample_boundary(),
            [
                task(
                    targets=[
                        "src/auth/service.ts",
                        "src/users/repository.ts",
                    ]
                )
            ],
            stage="implementation",
            expected_feature="001-login",
        )
        task_result = result["tasks"][0]
        self.assertEqual("CROSS_BOUNDARY", task_result["classification"])
        self.assertEqual(
            [
                {
                    "authority": "src/auth/auth.sdd",
                    "targets": ["src/auth/service.ts"],
                },
                {
                    "authority": "src/users/users.sdd",
                    "targets": ["src/users/repository.ts"],
                },
            ],
            task_result["authorityGroups"],
        )
        self.assertEqual([], result["diagnostics"])
        self.assertFalse(result["summary"]["blocking"])

    def test_invalid_write_metadata_blocks_implementation(self):
        result = validation.validate_feature(
            sample_boundary(),
            [task(write_metadata_errors=("duplicate Writes metadata",))],
            stage="implementation",
            expected_feature="001-login",
        )
        self.assertEqual("UNRESOLVED", result["tasks"][0]["classification"])
        self.assertEqual(
            ["INVALID_WRITE_DECLARATION"],
            [item["code"] for item in result["diagnostics"]],
        )
        self.assertTrue(result["summary"]["blocking"])

    def test_stale_task_target_blocks_implementation(self):
        result = validation.validate_feature(
            sample_boundary(),
            [task(targets=["src/auth/new-provider.ts"])],
            stage="implementation",
            expected_feature="001-login",
        )
        self.assertEqual("UNRESOLVED", result["tasks"][0]["classification"])
        stale = [
            item
            for item in result["diagnostics"]
            if item["code"] == "STALE_BOUNDARY"
        ]
        self.assertEqual(1, len(stale))
        self.assertEqual("blocking", stale[0]["severity"])
        self.assertTrue(result["summary"]["blocking"])

    def test_unknown_boundary_authority_blocks_implementation(self):
        boundary = sample_boundary()
        boundary["targets"] = []
        boundary["authorities"] = []
        boundary["crossBoundary"] = False
        boundary["unresolved"] = [
            {
                "input": "src/auth/service.ts",
                "normalizedPath": "src/auth/service.ts",
                "code": "AMBIGUOUS_AUTHORITY",
                "message": "multiple owners",
                "candidateAuthorities": [
                    "src/auth/auth.sdd",
                    "src/shared/shared.sdd",
                ],
            }
        ]
        result = validation.validate_feature(
            boundary,
            [task(targets=["src/auth/service.ts"])],
            stage="implementation",
            expected_feature="001-login",
        )
        codes = [item["code"] for item in result["diagnostics"]]
        self.assertIn("UNRESOLVED_TARGET", codes)
        self.assertIn("AUTHORITY_VIOLATION", codes)
        self.assertTrue(result["summary"]["blocking"])

    def test_intended_target_unsupported_fails_tasks_and_authorization(self):
        boundary = sample_boundary()
        path = "src/auth/new-provider.ts"
        boundary["targets"] = []
        boundary["authorities"] = []
        boundary["crossBoundary"] = False
        boundary["unresolved"] = [
            {
                "input": path,
                "normalizedPath": path,
                "code": "INTENDED_TARGET_UNSUPPORTED",
                "message": "provider cannot resolve the intended target",
            }
        ]
        records = [task(targets=[path])]

        task_result = validation.validate_feature(
            boundary,
            records,
            stage="tasks",
            expected_feature="001-login",
        )
        self.assertEqual(1, validation._result_exit_code(task_result, "error"))
        self.assertFalse(task_result["summary"]["blocking"])

        authorization_result = validation.validate_feature(
            boundary,
            records,
            stage="implementation",
            expected_feature="001-login",
        )
        self.assertEqual(
            1,
            validation._result_exit_code(authorization_result, "error"),
        )
        self.assertIn(
            "AUTHORITY_VIOLATION",
            [item["code"] for item in authorization_result["diagnostics"]],
        )
        self.assertTrue(authorization_result["summary"]["blocking"])

    def test_spec_only_task_does_not_require_non_spec_authority(self):
        result = validation.validate_feature(
            sample_boundary(),
            [task(targets=[], spec_targets=["src/auth/auth.sdd"])],
            stage="tasks",
            expected_feature="001-login",
        )
        self.assertEqual("SPEC_ONLY", result["tasks"][0]["classification"])
        self.assertEqual([], result["diagnostics"])

    def test_feature_mismatch_marks_boundary_stale(self):
        result = validation.validate_feature(
            sample_boundary(),
            [],
            stage="tasks",
            expected_feature="002-other",
        )
        self.assertEqual("STALE_BOUNDARY", result["diagnostics"][0]["code"])
        self.assertEqual("error", result["diagnostics"][0]["severity"])
