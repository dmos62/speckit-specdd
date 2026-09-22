import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from boundary_test_support import REPO_ROOT, boundary, validation


class BoundaryOutputTests(unittest.TestCase):
    def test_schema_validator_rejects_invalid_cross_boundary_state(self):
        schema = boundary.load_schema(REPO_ROOT)
        sample = {
            "schemaVersion": 1,
            "feature": "sample",
            "targets": [],
            "authorities": [],
            "crossBoundary": True,
            "unresolved": [],
        }
        metadata = boundary._generation_metadata(schema, "1.2.0", "1.5")
        if metadata is not None:
            sample[metadata[0]] = metadata[1]

        with self.assertRaisesRegex(
            boundary.BoundaryError,
            "does not satisfy its schema",
        ):
            boundary.validate_boundary(sample, schema)

    def test_intended_target_shapes_are_retained_when_resolver_lacks_support(self):
        schema = boundary.load_schema(REPO_ROOT)
        intended = (
            "src/exact.ts",
            "src/owned-directory/new.ts",
            "src/glob-match.ts",
            "src/no-owner.ts",
            "src/ambiguous.ts",
        )
        with tempfile.TemporaryDirectory() as temporary:
            payload = boundary.build_change_boundary(
                Path(temporary).resolve(),
                intended,
                feature="sample",
                schema=schema,
                cli_version="1.1.1",
                specdd_framework_version="1.5",
                intended_targets_supported=False,
            )

        self.assertEqual([], payload["targets"])
        self.assertEqual([], payload["authorities"])
        self.assertFalse(payload["crossBoundary"])
        records = {
            item["normalizedPath"]: item
            for item in payload["unresolved"]
        }
        self.assertEqual(set(intended), set(records))
        message = (
            "SpecDD CLI 1.1.1 does not expose complete typed intended-target "
            "resolution; the bridge will not infer pre-creation authority."
        )
        for path in intended:
            with self.subTest(path=path):
                self.assertEqual(
                    "INTENDED_TARGET_UNSUPPORTED",
                    records[path]["code"],
                )
                self.assertEqual(message, records[path]["message"])
                self.assertNotIn(
                    "INTENDED_TARGET_UNSUPPORTED",
                    records[path]["message"],
                )

    def test_validation_surfaces_intended_target_unsupported_boundary_code(self):
        schema = boundary.load_schema(REPO_ROOT)
        target = "src/future.ts"
        with tempfile.TemporaryDirectory() as temporary:
            payload = boundary.build_change_boundary(
                Path(temporary).resolve(),
                (target,),
                feature="sample",
                schema=schema,
                cli_version="1.1.1",
                specdd_framework_version="1.5",
                intended_targets_supported=False,
            )

        task = validation.TaskRecord(
            order=0,
            task_id="T001",
            story="US1",
            text="write future target",
            targets=(target,),
            spec_targets=(),
            invalid_targets=(),
        )
        result = validation.validate_feature(
            payload,
            [task],
            stage="implementation",
        )

        diagnostics = [
            item
            for item in result["diagnostics"]
            if item["code"] == "UNRESOLVED_TARGET"
            and item.get("boundaryCode") == "INTENDED_TARGET_UNSUPPORTED"
        ]
        self.assertEqual(1, len(diagnostics))
        self.assertNotIn(
            "INTENDED_TARGET_UNSUPPORTED",
            payload["unresolved"][0]["message"],
        )

    def test_intended_target_support_is_detected_from_resolve_help(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()

            def supported(args, **kwargs):
                return subprocess.CompletedProcess(
                    args,
                    0,
                    "--file --folder --sdd-file",
                    "",
                )

            def unsupported(args, **kwargs):
                return subprocess.CompletedProcess(args, 0, "--format json", "")

            self.assertTrue(
                boundary.specdd_resolve_supports_intended_targets(
                    root, "specdd", runner=supported
                )
            )
            self.assertFalse(
                boundary.specdd_resolve_supports_intended_targets(
                    root, "specdd", runner=unsupported
                )
            )

    def test_write_boundary_supports_stdout_and_file_modes(self):
        payload = {"schemaVersion": 1}
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            boundary.write_boundary(payload, "-")
        self.assertEqual('{\n  "schemaVersion": 1\n}\n', stdout.getvalue())

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "nested" / "boundary.json"
            boundary.write_boundary(payload, output)
            self.assertEqual(
                payload,
                json.loads(output.read_text(encoding="utf-8")),
            )

    def test_unresolved_record_uses_schema_field_names(self):
        schema = {
            "properties": {
                "unresolved": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/unresolved"},
                }
            },
            "$defs": {
                "unresolved": {
                    "type": "object",
                    "properties": {
                        "originalInput": {"type": "string"},
                        "normalizedPath": {"type": "string"},
                        "message": {"type": "string"},
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
                "generation": {"$ref": "#/$defs/generation"}
            },
            "$defs": {
                "generation": {
                    "type": "object",
                    "required": [
                        "specddCliVersion",
                        "specddFrameworkVersion",
                    ],
                    "properties": {
                        "specddCliVersion": {"type": "string"},
                        "specddFrameworkVersion": {"type": "string"},
                    },
                }
            },
        }
        self.assertEqual(
            (
                "generation",
                {
                    "specddCliVersion": "1.2.0",
                    "specddFrameworkVersion": "1.5",
                },
            ),
            boundary._generation_metadata(schema, "1.2.0", "1.5"),
        )

    def test_feature_boundary_is_ignored_and_untracked(self):
        probe = "specs/_specdd_boundary_probe_/.specdd/boundary.json"
        ignored = subprocess.run(
            ["git", "check-ignore", "--no-index", probe],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, ignored.returncode, ignored.stderr)

        tracked = subprocess.run(
            ["git", "ls-files", "specs/*/.specdd/boundary.json"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, tracked.returncode, tracked.stderr)
        self.assertEqual("", tracked.stdout.strip())

    def test_missing_specdd_cli_is_explicit_infrastructure_failure(self):
        with mock.patch("boundary_runtime.shutil.which", return_value=None):
            with self.assertRaisesRegex(
                boundary.BoundaryError,
                "Required SpecDD CLI executable was not found",
            ) as raised:
                boundary._locate_executable("specdd-missing")
        self.assertIn("bash scripts/bootstrap.sh", str(raised.exception))
