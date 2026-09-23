import copy
import unittest

from boundary_test_fixture import RealFixtureIntegrationTests
from boundary_test_output import BoundaryOutputTests
from boundary_test_ownership import OwnershipProjectionTests
from boundary_test_paths import BoundaryNormalizationTests
from boundary_test_resolver import ResolverProjectionTests
from boundary_test_support import REPO_ROOT, boundary


def semantic_boundary():
    return {
        "schemaVersion": 1,
        "feature": "sample",
        "targets": [
            {
                "path": "src/auth/service.ts",
                "primaryAuthority": "src/auth/auth.sdd",
                "resolvedSpecs": [
                    "project.sdd",
                    "src/auth/auth.sdd",
                ],
            }
        ],
        "authorities": ["src/auth/auth.sdd"],
        "crossBoundary": False,
        "unresolved": [],
        "generation": {
            "specddCliVersion": "1.2.0",
            "specddFrameworkVersion": "1.5",
        },
    }


class BoundarySemanticConsistencyTests(unittest.TestCase):
    def test_shape_valid_semantic_corruption_is_rejected(self):
        schema = boundary.load_schema(REPO_ROOT)
        cases = {}

        candidate = semantic_boundary()
        candidate["targets"].append(copy.deepcopy(candidate["targets"][0]))
        cases["duplicate target path"] = candidate

        candidate = semantic_boundary()
        candidate["authorities"] = ["src/users/users.sdd"]
        cases["authority projection mismatch"] = candidate

        candidate = semantic_boundary()
        candidate["targets"][0]["resolvedSpecs"] = ["project.sdd"]
        cases["authority absent from resolved specs"] = candidate

        candidate = semantic_boundary()
        candidate["unresolved"] = [
            {
                "input": "src/auth/service.ts",
                "normalizedPath": "src/auth/service.ts",
                "code": "UNRESOLVED_TARGET",
                "message": "unresolved",
            }
        ]
        cases["resolved and unresolved overlap"] = candidate

        candidate = semantic_boundary()
        candidate["targets"] = []
        candidate["authorities"] = []
        candidate["unresolved"] = [
            {
                "input": "src/shared/service.ts",
                "normalizedPath": "src/shared/service.ts",
                "code": "AMBIGUOUS_AUTHORITY",
                "message": "ambiguous",
                "candidateAuthorities": ["src/auth/auth.sdd"],
            }
        ]
        cases["ambiguous authority needs two candidates"] = candidate

        candidate = copy.deepcopy(candidate)
        candidate["unresolved"][0]["code"] = "UNRESOLVED_TARGET"
        cases["candidates require ambiguity"] = candidate

        for label, candidate in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    [],
                    boundary._schema_errors(candidate, schema, schema, "$"),
                )
                with self.assertRaisesRegex(
                    boundary.BoundaryError,
                    "semantically inconsistent",
                ):
                    boundary.validate_boundary(candidate, schema)


__all__ = [
    "BoundaryNormalizationTests",
    "BoundaryOutputTests",
    "BoundarySemanticConsistencyTests",
    "OwnershipProjectionTests",
    "RealFixtureIntegrationTests",
    "ResolverProjectionTests",
]


if __name__ == "__main__":
    unittest.main()
