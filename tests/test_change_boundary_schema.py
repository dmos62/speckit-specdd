import copy
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "integration" / "specdd" / "schemas" / "change-boundary.schema.json"


class SchemaValidationError(AssertionError):
    pass


def _json_equal(left, right):
    return type(left) is type(right) and left == right


def _type_matches(value, expected):
    checks = {
        "array": lambda candidate: isinstance(candidate, list),
        "boolean": lambda candidate: isinstance(candidate, bool),
        "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
        "null": lambda candidate: candidate is None,
        "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
        "object": lambda candidate: isinstance(candidate, dict),
        "string": lambda candidate: isinstance(candidate, str),
    }
    return checks[expected](value)


class MinimalDraft202012Validator:
    """Validate the JSON Schema keywords used by Change Boundary v1.

    The production adapter will choose its runtime validator in Phase 4. This small
    contract harness keeps the schema tests dependency-free until that adapter exists.
    """

    def __init__(self, schema):
        self.root = schema

    def validate(self, instance):
        self._validate(self.root, instance, "$")

    def _resolve_ref(self, reference):
        if not reference.startswith("#/"):
            raise SchemaValidationError(f"unsupported reference {reference!r}")
        node = self.root
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            node = node[token]
        return node

    def _validate(self, schema, instance, path):
        if "$ref" in schema:
            self._validate(self._resolve_ref(schema["$ref"]), instance, path)

        for index, subschema in enumerate(schema.get("allOf", [])):
            self._validate(subschema, instance, f"{path}.allOf[{index}]")

        if "anyOf" in schema and not any(
            self._matches(subschema, instance, path) for subschema in schema["anyOf"]
        ):
            raise SchemaValidationError(f"{path}: no anyOf branch matched")

        if "if" in schema and self._matches(schema["if"], instance, path):
            if "then" in schema:
                self._validate(schema["then"], instance, path)

        if "const" in schema and not _json_equal(instance, schema["const"]):
            raise SchemaValidationError(f"{path}: expected const {schema['const']!r}")

        if "enum" in schema and not any(
            _json_equal(instance, value) for value in schema["enum"]
        ):
            raise SchemaValidationError(f"{path}: value is not in enum")

        expected_type = schema.get("type")
        if expected_type is not None and not _type_matches(instance, expected_type):
            raise SchemaValidationError(f"{path}: expected {expected_type}")

        if isinstance(instance, str):
            if len(instance) < schema.get("minLength", 0):
                raise SchemaValidationError(f"{path}: string is shorter than minLength")
            pattern = schema.get("pattern")
            if pattern is not None and re.search(pattern, instance) is None:
                raise SchemaValidationError(
                    f"{path}: string does not match pattern {pattern!r}"
                )

        if isinstance(instance, list):
            if len(instance) < schema.get("minItems", 0):
                raise SchemaValidationError(f"{path}: array is shorter than minItems")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                raise SchemaValidationError(f"{path}: array is longer than maxItems")
            if schema.get("uniqueItems"):
                encoded = [
                    json.dumps(value, sort_keys=True, separators=(",", ":"))
                    for value in instance
                ]
                if len(encoded) != len(set(encoded)):
                    raise SchemaValidationError(f"{path}: array items are not unique")
            if "items" in schema:
                for index, value in enumerate(instance):
                    self._validate(schema["items"], value, f"{path}[{index}]")

        if isinstance(instance, dict):
            required = schema.get("required", [])
            missing = [name for name in required if name not in instance]
            if missing:
                raise SchemaValidationError(
                    f"{path}: missing required properties {missing}"
                )

            properties = schema.get("properties", {})
            if schema.get("additionalProperties") is False:
                unexpected = sorted(set(instance) - set(properties))
                if unexpected:
                    raise SchemaValidationError(
                        f"{path}: unexpected properties {unexpected}"
                    )

            for name, subschema in properties.items():
                if name in instance:
                    self._validate(subschema, instance[name], f"{path}.{name}")

    def _matches(self, schema, instance, path):
        try:
            self._validate(schema, instance, path)
        except SchemaValidationError:
            return False
        return True


def boundary(**overrides):
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
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.validator = MinimalDraft202012Validator(cls.schema)

    def assertValid(self, instance):
        self.validator.validate(instance)

    def assertInvalid(self, instance):
        with self.assertRaises(SchemaValidationError):
            self.validator.validate(instance)

    def test_uses_draft_2020_12_and_version_one(self):
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertEqual(self.schema["properties"]["schemaVersion"]["const"], 1)

    def test_generation_records_tool_versions_without_nondeterministic_timestamp(self):
        generation = self.schema["$defs"]["generation"]
        self.assertEqual(
            generation["required"],
            ["specddCliVersion", "specddFrameworkVersion"],
        )
        self.assertNotIn("generatedAt", generation["properties"])

    def test_accepts_one_authority_boundary(self):
        self.assertValid(boundary())

    def test_accepts_multiple_authorities_and_cross_boundary_feature(self):
        candidate = boundary(
            targets=[
                {
                    "path": "src/auth/service.ts",
                    "primaryAuthority": "src/auth/auth.sdd",
                    "resolvedSpecs": ["project.sdd", "src/auth/auth.sdd"],
                },
                {
                    "path": "src/users/repository.ts",
                    "primaryAuthority": "src/users/users.sdd",
                    "resolvedSpecs": ["project.sdd", "src/users/users.sdd"],
                },
            ],
            authorities=["src/auth/auth.sdd", "src/users/users.sdd"],
            crossBoundary=True,
        )
        self.assertValid(candidate)

    def test_accepts_unresolved_target_without_forcing_invalid_input_into_normalized_path(self):
        candidate = boundary(
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
        self.assertValid(candidate)

    def test_accepts_resolved_target_without_determinable_primary_authority(self):
        candidate = boundary(
            targets=[
                {
                    "path": "src/shared/contract.ts",
                    "primaryAuthority": None,
                    "resolvedSpecs": ["project.sdd"],
                }
            ],
            authorities=[],
        )
        self.assertValid(candidate)

    def test_rejects_absolute_or_dot_segment_repository_paths(self):
        for invalid_path in (
            "/src/auth/service.ts",
            "C:/repo/src/auth/service.ts",
            "src/../users/repository.ts",
            "./src/auth/service.ts",
            "src\\auth\\service.ts",
        ):
            with self.subTest(invalid_path=invalid_path):
                candidate = boundary()
                candidate["targets"] = copy.deepcopy(candidate["targets"])
                candidate["targets"][0]["path"] = invalid_path
                self.assertInvalid(candidate)

    def test_rejects_cross_boundary_flag_that_disagrees_with_authority_count(self):
        self.assertInvalid(boundary(crossBoundary=True))
        self.assertInvalid(
            boundary(
                authorities=["src/auth/auth.sdd", "src/users/users.sdd"],
                crossBoundary=False,
            )
        )

    def test_rejects_duplicate_authorities_and_unknown_fields(self):
        self.assertInvalid(
            boundary(authorities=["src/auth/auth.sdd", "src/auth/auth.sdd"])
        )
        candidate = boundary()
        candidate["copiedMustRules"] = ["do not duplicate SpecDD"]
        self.assertInvalid(candidate)


if __name__ == "__main__":
    unittest.main()
