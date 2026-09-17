import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from boundary_test_support import (
    REPO_ROOT,
    boundary,
)


class BoundaryOutputTests(unittest.TestCase):
    def test_schema_validator_rejects_invalid_cross_boundary_state(self):
        schema = boundary.load_schema(
            REPO_ROOT
        )
        sample = {
            "schemaVersion": 1,
            "feature": "sample",
            "targets": [],
            "authorities": [],
            "crossBoundary": True,
            "unresolved": [],
        }

        metadata = boundary._generation_metadata(
            schema,
            "1.1.1",
            "1.5",
        )
        if metadata is not None:
            sample[metadata[0]] = metadata[1]

        with self.assertRaisesRegex(
            boundary.BoundaryError,
            "does not satisfy its schema",
        ):
            boundary.validate_boundary(
                sample,
                schema,
            )

    def test_missing_target_is_preserved_as_structured_unresolved(self):
        schema = boundary.load_schema(
            REPO_ROOT
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(
                temporary
            ).resolve()
            payload = boundary.build_change_boundary(
                root,
                ["src/missing.ts"],
                feature="sample",
                schema=schema,
                cli_version="1.1.1",
                specdd_framework_version="1.5",
            )

        self.assertEqual(
            [],
            payload["targets"],
        )
        self.assertEqual(
            [],
            payload["authorities"],
        )
        self.assertFalse(
            payload["crossBoundary"]
        )
        self.assertEqual(
            {
                "input": "src/missing.ts",
                "normalizedPath": "src/missing.ts",
                "code": "UNRESOLVED_TARGET",
                "message": (
                    "Target does not exist; "
                    "SpecDD resolve requires existing targets"
                ),
            },
            payload["unresolved"][0],
        )

    def test_write_boundary_supports_stdout_and_file_modes(self):
        payload = {
            "schemaVersion": 1,
        }

        stdout = io.StringIO()
        with contextlib.redirect_stdout(
            stdout
        ):
            boundary.write_boundary(
                payload,
                "-",
            )

        self.assertEqual(
            '{\n  "schemaVersion": 1\n}\n',
            stdout.getvalue(),
        )

        with tempfile.TemporaryDirectory() as temporary:
            output = (
                Path(temporary)
                / "nested"
                / "boundary.json"
            )

            boundary.write_boundary(
                payload,
                output,
            )

            self.assertEqual(
                payload,
                json.loads(
                    output.read_text(
                        encoding="utf-8"
                    )
                ),
            )

    def test_unresolved_record_uses_schema_field_names(self):
        schema = {
            "properties": {
                "unresolved": {
                    "type": "array",
                    "items": {
                        "$ref": "#/$defs/unresolved",
                    },
                }
            },
            "$defs": {
                "unresolved": {
                    "type": "object",
                    "properties": {
                        "originalInput": {
                            "type": "string",
                        },
                        "normalizedPath": {
                            "type": "string",
                        },
                        "message": {
                            "type": "string",
                        },
                    },
                }
            },
        }

        self.assertEqual(
            {
                "originalInput": "src\\missing.ts",
                "normalizedPath": "src/missing.ts",
                "message": "missing",
            },
            boundary._unresolved_record(
                boundary.Unresolved(
                    input="src\\missing.ts",
                    code="UNRESOLVED_TARGET",
                    message="missing",
                    path="src/missing.ts",
                ),
                schema,
            ),
        )

    def test_generation_metadata_supports_schema_reference(self):
        schema = {
            "properties": {
                "generation": {
                    "$ref": "#/$defs/generation",
                }
            },
            "$defs": {
                "generation": {
                    "type": "object",
                    "required": [
                        "specddCliVersion",
                        "specddFrameworkVersion",
                    ],
                    "properties": {
                        "specddCliVersion": {
                            "type": "string",
                        },
                        "specddFrameworkVersion": {
                            "type": "string",
                        },
                    },
                }
            },
        }

        self.assertEqual(
            (
                "generation",
                {
                    "specddCliVersion": "1.1.1",
                    "specddFrameworkVersion": "1.5",
                },
            ),
            boundary._generation_metadata(
                schema,
                "1.1.1",
                "1.5",
            ),
        )
