import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from boundary_test_support import (
    validation,
    verification,
    workflow_gate,
)


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
                result(error=1),
                "error",
            ),
        )
        self.assertEqual(
            1,
            validation._result_exit_code(
                result(blocking=1),
                "error",
            ),
        )

    def test_validation_warning_remains_non_failing(self):
        self.assertEqual(
            0,
            validation._result_exit_code(
                result(warning=1),
                "error",
            ),
        )

    def test_verification_error_threshold_fails_for_errors_and_blocks(self):
        self.assertEqual(
            1,
            verification._result_exit_code(
                result(error=1),
                "error",
            ),
        )
        self.assertEqual(
            1,
            verification._result_exit_code(
                result(blocking=1),
                "error",
            ),
        )

    def test_blocking_threshold_does_not_promote_nonblocking_error(self):
        self.assertEqual(
            0,
            verification._result_exit_code(
                result(error=1),
                "blocking",
            ),
        )
        self.assertEqual(
            1,
            verification._result_exit_code(
                result(blocking=1),
                "blocking",
            ),
        )


class WorkflowFeaturePathTests(unittest.TestCase):
    def test_active_feature_normalizes_relative_backslash_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            feature_dir = root / "specs" / "001 login"
            feature_dir.mkdir(parents=True)

            with mock.patch.dict(
                os.environ,
                {"SPECIFY_FEATURE_DIRECTORY": r"specs\001 login"},
                clear=False,
            ):
                feature, resolved, relative = workflow_gate._active_feature(root)

            self.assertEqual("001 login", feature)
            self.assertEqual(feature_dir, resolved)
            self.assertEqual("specs/001 login", relative)

    @unittest.skipUnless(
        os.name == "nt",
        "Drive-qualified active feature evidence requires Windows",
    )
    def test_active_feature_accepts_drive_qualified_absolute_path_on_windows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            feature_dir = root / "specs" / "001-login"
            feature_dir.mkdir(parents=True)

            for configured in (str(feature_dir), feature_dir.as_posix()):
                with self.subTest(configured=configured):
                    with mock.patch.dict(
                        os.environ,
                        {"SPECIFY_FEATURE_DIRECTORY": configured},
                        clear=False,
                    ):
                        feature, resolved, relative = workflow_gate._active_feature(root)

                    self.assertEqual("001-login", feature)
                    self.assertEqual(feature_dir, resolved)
                    self.assertEqual("specs/001-login", relative)

    def test_active_feature_rejects_foreign_absolute_path_style(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            foreign = (
                "/tmp/specdd-foreign/specs/001-login"
                if os.name == "nt"
                else r"C:\specdd-foreign\specs\001-login"
            )
            style = "POSIX" if os.name == "nt" else "Windows"

            with mock.patch.dict(
                os.environ,
                {"SPECIFY_FEATURE_DIRECTORY": foreign},
                clear=False,
            ):
                with self.assertRaisesRegex(
                    workflow_gate.WorkflowGateError,
                    f"absolute {style} path on this host",
                ):
                    workflow_gate._active_feature(root)
