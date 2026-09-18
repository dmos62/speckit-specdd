import copy
import json
import unittest
from pathlib import Path

from boundary_test_support import boundary as boundary_adapter


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    ROOT
    / "integration"
    / "specdd"
    / "schemas"
    / "change-boundary.schema.json"
)


def boundary_document(**overrides):
    value = {
        "schemaVersion": 1,
        "feature": "001-google-login",
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
            "specddCliVersion": "1.1.1",
            "specddFrameworkVersion": "1.5",
        },
    }
    value.update(overrides)
    return value


class ChangeBoundarySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )

    def assertValid(self, instance):
        boundary_adapter.validate_boundary(
            instance,
            self.schema,
        )

    def assertInvalid(self, instance):
        with self.assertRaises(
            boundary_adapter.BoundaryError
        ):
            boundary_adapter.validate_boundary(
                instance,
                self.schema,
            )

    def test_uses_draft_2020_12_and_version_one(self):
        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            self.schema["$schema"],
        )
        self.assertEqual(
            1,
            self.schema["properties"]["schemaVersion"]["const"],
        )

    def test_generation_records_versions_without_timestamp(self):
        generation = self.schema["$defs"]["generation"]
        self.assertEqual(
            [
                "specddCliVersion",
                "specddFrameworkVersion",
            ],
            generation["required"],
        )
        self.assertNotIn(
            "generatedAt",
            generation["properties"],
        )

    def test_accepts_one_authority_boundary(self):
        self.assertValid(
            boundary_document()
        )

    def test_accepts_multiple_authorities(self):
        self.assertValid(
            boundary_document(
                targets=[
                    {
                        "path": "src/auth/service.ts",
                        "primaryAuthority": "src/auth/auth.sdd",
                        "resolvedSpecs": [
                            "project.sdd",
                            "src/auth/auth.sdd",
                        ],
                    },
                    {
                        "path": "src/users/repository.ts",
                        "primaryAuthority": "src/users/users.sdd",
                        "resolvedSpecs": [
                            "project.sdd",
                            "src/users/users.sdd",
                        ],
                    },
                ],
                authorities=[
                    "src/auth/auth.sdd",
                    "src/users/users.sdd",
                ],
                crossBoundary=True,
            )
        )

    def test_accepts_supported_unresolved_and_nullable_authority_shapes(self):
        self.assertValid(
            boundary_document(
                targets=[],
                authorities=[],
                unresolved=[
                    {
                        "input": "../outside/repository.ts",
                        "code": "INVALID_TARGET",
                        "message": "target escapes repository root",
                    }
                ],
            )
        )
        self.assertValid(
            boundary_document(
                targets=[
                    {
                        "path": "src/shared/contract.ts",
                        "primaryAuthority": None,
                        "resolvedSpecs": ["project.sdd"],
                    }
                ],
                authorities=[],
            )
        )

    def test_rejects_noncanonical_repository_paths(self):
        for invalid_path in (
            "/src/auth/service.ts",
            "C:/repo/src/auth/service.ts",
            "src/../users/repository.ts",
            "./src/auth/service.ts",
            "src\\auth\\service.ts",
        ):
            with self.subTest(
                invalid_path=invalid_path
            ):
                candidate = boundary_document()
                candidate["targets"] = copy.deepcopy(
                    candidate["targets"]
                )
                candidate["targets"][0]["path"] = invalid_path
                self.assertInvalid(candidate)

    def test_rejects_cross_boundary_flag_mismatch(self):
        self.assertInvalid(
            boundary_document(
                crossBoundary=True
            )
        )
        self.assertInvalid(
            boundary_document(
                authorities=[
                    "src/auth/auth.sdd",
                    "src/users/users.sdd",
                ],
                crossBoundary=False,
            )
        )

    def test_rejects_duplicate_authorities_and_unknown_fields(self):
        self.assertInvalid(
            boundary_document(
                authorities=[
                    "src/auth/auth.sdd",
                    "src/auth/auth.sdd",
                ]
            )
        )

        candidate = boundary_document()
        candidate["copiedMustRules"] = [
            "do not duplicate SpecDD"
        ]
        self.assertInvalid(candidate)


if __name__ == "__main__":
    unittest.main()
