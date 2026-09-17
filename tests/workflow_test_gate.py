import unittest

from boundary_test_support import (
    validation,
    verification,
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
