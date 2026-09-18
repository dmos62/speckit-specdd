import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from boundary_test_support import (
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

    def test_authorization_snapshot_survives_boundary_refresh_and_failed_reauthorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()
            subprocess.run(
                [
                    "git",
                    "init",
                    "-q",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            feature_dir = (
                root
                / "specs"
                / "001-login"
            )
            boundary_path = (
                feature_dir
                / ".specdd"
                / "boundary.json"
            )
            task_path = (
                feature_dir
                / "tasks.md"
            )
            boundary_path.parent.mkdir(
                parents=True
            )
            task_path.write_text(
                "- [ ] T001 [US1] Update src/auth/service.ts\n",
                encoding="utf-8",
            )

            authorized = {
                "schemaVersion": 1,
                "feature": "001-login",
                "targets": [
                    {
                        "path": "src/auth/service.ts",
                        "primaryAuthority": "src/auth/auth.sdd",
                        "resolvedSpecs": [
                            "src/auth/auth.sdd",
                        ],
                    }
                ],
                "authorities": [
                    "src/auth/auth.sdd",
                ],
                "crossBoundary": False,
                "unresolved": [],
                "generation": {
                    "specddCliVersion": "1.1.1",
                    "specddFrameworkVersion": "1.5",
                },
            }
            boundary_path.write_text(
                json.dumps(
                    authorized
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            errors = io.StringIO()
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "SPECIFY_FEATURE_DIRECTORY": "specs/001-login",
                    },
                    clear=False,
                ),
                contextlib.redirect_stdout(
                    output
                ),
                contextlib.redirect_stderr(
                    errors
                ),
            ):
                status = workflow_gate.run_stage(
                    root,
                    "authorize",
                )

            self.assertEqual(
                0,
                status,
            )
            snapshot_path = (
                verification.authorization_snapshot_path(
                    root
                )
            )
            stored = json.loads(
                snapshot_path.read_text(
                    encoding="utf-8",
                )
            )
            self.assertEqual(
                authorized,
                stored,
            )

            refreshed = {
                **authorized,
                "targets": [
                    {
                        "path": "src/users/repository.ts",
                        "primaryAuthority": "src/users/users.sdd",
                        "resolvedSpecs": [
                            "src/users/users.sdd",
                        ],
                    }
                ],
                "authorities": [
                    "src/users/users.sdd",
                ],
            }
            boundary_path.write_text(
                json.dumps(
                    refreshed
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "SPECIFY_FEATURE_DIRECTORY": "specs/001-login",
                    },
                    clear=False,
                ),
                contextlib.redirect_stdout(
                    io.StringIO()
                ),
                contextlib.redirect_stderr(
                    io.StringIO()
                ),
            ):
                failed_status = workflow_gate.run_stage(
                    root,
                    "authorize",
                )

            self.assertEqual(
                1,
                failed_status,
            )
            self.assertEqual(
                stored,
                json.loads(
                    snapshot_path.read_text(
                        encoding="utf-8",
                    )
                ),
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
