import unittest

from validation_test_engine import (
    ValidationEngineTests,
)
from validation_test_fixture import (
    RealFixtureValidationTests,
)
from validation_test_tasks import (
    ValidationTaskParsingTests,
)

__all__ = [
    "RealFixtureValidationTests",
    "ValidationEngineTests",
    "ValidationTaskParsingTests",
]


if __name__ == "__main__":
    unittest.main()
