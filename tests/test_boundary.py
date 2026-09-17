import unittest

from boundary_test_fixture import (
    RealFixtureIntegrationTests,
)
from boundary_test_output import (
    BoundaryOutputTests,
)
from boundary_test_paths import (
    BoundaryNormalizationTests,
)
from boundary_test_resolver import (
    ResolverProjectionTests,
)

__all__ = [
    "BoundaryNormalizationTests",
    "BoundaryOutputTests",
    "RealFixtureIntegrationTests",
    "ResolverProjectionTests",
]


if __name__ == "__main__":
    unittest.main()
