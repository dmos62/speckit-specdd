import unittest

from verification_test_engine import (
    VerificationEngineTests,
)
from verification_test_fixture import (
    RealFixtureVerificationTests,
)
from verification_test_git import (
    VerificationGitTests,
)

__all__ = [
    "RealFixtureVerificationTests",
    "VerificationEngineTests",
    "VerificationGitTests",
]


if __name__ == "__main__":
    unittest.main()
