import unittest

from workflow_test_gate import (
    WorkflowFeaturePathTests,
    WorkflowGateExitTests,
)
from workflow_test_source import (
    WorkflowSourceTests,
)

__all__ = [
    "WorkflowFeaturePathTests",
    "WorkflowGateExitTests",
    "WorkflowSourceTests",
]


if __name__ == "__main__":
    unittest.main()
