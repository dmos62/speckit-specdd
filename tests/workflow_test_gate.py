import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from boundary_test_support import (
    REPO_ROOT,
    boundary,
    validation,
    verification,
    workflow_gate,
)
from validation_cli import _serialize as serialize_validation
from verification_cli import _serialize as serialize_verification


def result(
    *,
    warning=0,
    error=0,
    blocking=0,
):
    return {
        "summary": {
            "countsBySeverity": {
                "info": 0,
                "warning": warning,
                "error": error,
                "blocking": blocking,
            }
        }
    }


class WorkflowGateExitTests(unittest.TestCase):
    def test_validation_error_threshold_fails_for_errors_and_blocks(self):
        self.assertEqual(
            1,
            validation._result_exit_code(
                result(
                    error=1
                ),
                "error",
            ),
        )
        self.assertEqual(
            1,
            validation._result_exit_code(
                result(
                    blocking=1
                ),
                "error",
            ),
        )

    def test_validation_warning_remains_non_failing(self):
        self.assertEqual(
            0,
            validation._result_exit_code(
                result(
                    warning=1
                ),
                "error",
            ),
        )

    def test_verification_error_threshold_fails_for_errors_and_blocks(self):
        self.assertEqual(
            1,
            verification._result_exit_code(
                result(
                    error=1
                ),
                "error",
            ),
        )
        self.assertEqual(
            1,
            verification._result_exit_code(
                result(
                    blocking=1
                ),
                "error",
            ),
        )

    def test_blocking_threshold_does_not_promote_nonblocking_error(self):
        self.assertEqual(
            0,
            verification._result_exit_code(
                result(
                    error=1
                ),
                "blocking",
            ),
        )
        self.assertEqual(
            1,
            verification._result_exit_code(
                result(
                    blocking=1
                ),
                "blocking",
            ),
        )

    def test_bridge_json_serializers_ignore_mapping_insertion_order(self):
        first = {
            "zeta": 1,
            "alpha": {
                "zeta": 2,
                "alpha": 3,
            },
        }
        second = {
            "alpha": {
                "alpha": 3,
                "zeta": 2,
            },
            "zeta": 1,
        }

        for serializer in (
            serialize_validation,
            serialize_verification,
        ):
            with self.subTest(
                serializer=serializer.__module__
            ):
                self.assertEqual(
                    serializer(
                        first
                    ),
                    serializer(
                        second
                    ),
                )
                self.assertTrue(
                    serializer(
                        first
                    ).endswith(
                        "\n"
                    )
                )

    def test_task_stage_boundary_can_represent_empty_write_scope_without_framework_bootstrap(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.assertFalse(
                (root / ".specdd" / "bootstrap.md").exists()
            )

            value = boundary.build_change_boundary(
                root,
                (),
                feature="001-empty",
                schema=boundary.load_schema(REPO_ROOT),
                cli_version="1.1.1",
                allow_empty=True,
            )

        self.assertEqual([], value["targets"])
        self.assertEqual([], value["authorities"])
        self.assertEqual([], value["unresolved"])
        self.assertFalse(value["crossBoundary"])
        self.assertEqual(
            "not-required",
            value["generation"]["specddFrameworkVersion"],
        )


class WorkflowFeaturePathTests(unittest.TestCase):
    def test_active_feature_normalizes_relative_backslash_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()
            feature_dir = (
                root
                / "specs"
                / "001 login"
            )
            feature_dir.mkdir(
                parents=True
            )

            with mock.patch.dict(
                os.environ,
                {
                    "SPECIFY_FEATURE_DIRECTORY": r"specs\001 login",
                },
                clear=False,
            ):
                (
                    feature,
                    resolved,
                    relative,
                ) = workflow_gate._active_feature(
                    root
                )

            self.assertEqual(
                "001 login",
                feature,
            )
            self.assertEqual(
                feature_dir,
                resolved,
            )
            self.assertEqual(
                "specs/001 login",
                relative,
            )

    def test_boundary_summary_uses_repository_relative_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()
            boundary_path = (
                root
                / "specs"
                / "001-login"
                / ".specdd"
                / "boundary.json"
            )
            value = {
                "targets": [],
                "authorities": [],
                "crossBoundary": False,
                "unresolved": [],
            }

            summary = workflow_gate._boundary_summary(
                root,
                "001-login",
                boundary_path,
                value,
            )

            self.assertEqual(
                "specs/001-login/.specdd/boundary.json",
                summary["boundary"],
            )

    @unittest.skipUnless(
        os.name == "nt",
        "Drive-qualified active feature evidence requires Windows",
    )
    def test_active_feature_accepts_drive_qualified_absolute_path_on_windows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()
            feature_dir = (
                root
                / "specs"
                / "001-login"
            )
            feature_dir.mkdir(
                parents=True
            )

            for configured in (
                str(
                    feature_dir
                ),
                feature_dir.as_posix(),
            ):
                with self.subTest(
                    configured=configured
                ):
                    with mock.patch.dict(
                        os.environ,
                        {
                            "SPECIFY_FEATURE_DIRECTORY": configured,
                        },
                        clear=False,
                    ):
                        (
                            feature,
                            resolved,
                            relative,
                        ) = workflow_gate._active_feature(
                            root
                        )

                    self.assertEqual(
                        "001-login",
                        feature,
                    )
                    self.assertEqual(
                        feature_dir,
                        resolved,
                    )
                    self.assertEqual(
                        "specs/001-login",
                        relative,
                    )

    def test_active_feature_rejects_foreign_absolute_path_style(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()
            foreign = (
                "/tmp/specdd-foreign/specs/001-login"
                if os.name == "nt"
                else r"C:\specdd-foreign\specs\001-login"
            )
            style = (
                "POSIX"
                if os.name == "nt"
                else "Windows"
            )

            with mock.patch.dict(
                os.environ,
                {
                    "SPECIFY_FEATURE_DIRECTORY": foreign,
                },
                clear=False,
            ):
                with self.assertRaisesRegex(
                    workflow_gate.WorkflowGateError,
                    f"absolute {style} path on this host",
                ):
                    workflow_gate._active_feature(
                        root
                    )
