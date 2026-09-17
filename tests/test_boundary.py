import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "integration" / "specdd" / "scripts" / "boundary.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "specdd-two-domain"

module_spec = importlib.util.spec_from_file_location("specdd_boundary", SCRIPT_PATH)
boundary = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = boundary
module_spec.loader.exec_module(boundary)


class BoundaryNormalizationTests(unittest.TestCase):
    def test_discovers_specdd_root_without_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "repo"
            nested = root / "src" / "auth"
            nested.mkdir(parents=True)
            bootstrap = root / ".specdd" / "bootstrap.md"
            bootstrap.parent.mkdir()
            bootstrap.write_text(
                "---\nVersion: 1.5\n---\n",
                encoding="utf-8",
            )

            self.assertEqual(
                root,
                boundary.discover_repository_root(nested),
            )

    def test_normalizes_repository_relative_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "src" / "auth" / "service.ts"
            target.parent.mkdir(parents=True)
            target.touch()

            result = boundary.normalize_target(
                root,
                "src\\auth\\service.ts",
            )

            self.assertEqual(
                "src/auth/service.ts",
                result.path,
            )
            self.assertEqual(
                target,
                result.absolute_path,
            )

    def test_rejects_target_outside_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            root = parent / "repo"
            root.mkdir()
            outside = parent / "outside.ts"
            outside.touch()

            with self.assertRaisesRegex(
                boundary.BoundaryError,
                "outside repository root",
            ):
                boundary.normalize_target(
                    root,
                    str(outside),
                )

    def test_normalizes_resolver_spec_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()

            self.assertEqual(
                "src/auth/auth.sdd",
                boundary.normalize_resolver_path(
                    root,
                    "src\\auth\\auth.sdd",
                    spec=True,
                ),
            )


class ResolverProjectionTests(unittest.TestCase):
    def test_extracts_compact_resolver_sections_and_derives_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            service = root / "src" / "auth" / "service.ts"
            service.parent.mkdir(parents=True)
            service.touch()

            payload = {
                "directories": [
                    {
                        "path": "/",
                        "specs": [
                            {
                                "path": "fixture.sdd",
                                "sections": {
                                    "Owns": [
                                        {
                                            "body": [
                                                "./README.md",
                                            ]
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                    {
                        "path": "/src/auth/",
                        "specs": [
                            {
                                "path": "src/auth/auth.sdd",
                                "sections": {
                                    "Owns": [
                                        {
                                            "body": [
                                                "./*.ts",
                                            ]
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                ]
            }

            specs = boundary.extract_resolved_specs(
                payload,
                root,
            )
            authority, owners = boundary.derive_primary_authority(
                root,
                "src/auth/service.ts",
                specs,
            )

            self.assertEqual(
                [
                    "fixture.sdd",
                    "src/auth/auth.sdd",
                ],
                [
                    item["path"]
                    for item in specs
                ],
            )
            self.assertEqual(
                "src/auth/auth.sdd",
                authority,
            )
            self.assertEqual(
                ["src/auth/auth.sdd"],
                owners,
            )

    def test_specdd_globstar_matches_nested_targets(self):
        self.assertTrue(
            boundary._glob_matches(
                "src/auth/**",
                "src/auth/deep/service.ts",
            )
        )
        self.assertTrue(
            boundary._glob_matches(
                "src/auth/**/*",
                "src/auth/deep/nested/service.ts",
            )
        )
        self.assertTrue(
            boundary._glob_matches(
                "src/**/service.{ts,js}",
                "src/auth/deep/service.ts",
            )
        )
        self.assertFalse(
            boundary._glob_matches(
                "src/auth/*.ts",
                "src/auth/deep/service.ts",
            )
        )

    def test_detects_multiple_ownership_claims(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "src" / "auth" / "service.ts"
            target.parent.mkdir(parents=True)
            target.touch()

            specs = [
                {
                    "path": "root.sdd",
                    "sections": {
                        "Owns": [
                            {
                                "body": [
                                    "./src/auth",
                                ]
                            }
                        ]
                    },
                },
                {
                    "path": "src/auth/auth.sdd",
                    "sections": {
                        "Owns": [
                            {
                                "body": [
                                    "./service.ts",
                                ]
                            }
                        ]
                    },
                },
            ]

            authority, owners = boundary.derive_primary_authority(
                root,
                "src/auth/service.ts",
                specs,
            )

            self.assertIsNone(authority)
            self.assertEqual(
                [
                    "root.sdd",
                    "src/auth/auth.sdd",
                ],
                owners,
            )

    def test_nonzero_resolver_exit_becomes_unresolved_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target_path = root / "src" / "auth" / "service.ts"
            target_path.parent.mkdir(parents=True)
            target_path.touch()
            target = boundary.normalize_target(
                root,
                "src/auth/service.ts",
            )

            def runner(args, **kwargs):
                return subprocess.CompletedProcess(
                    args,
                    1,
                    "",
                    "resolver failed\nwith detail",
                )

            specs, error = boundary.resolve_target(
                root,
                target,
                "specdd",
                runner=runner,
            )

            self.assertIsNone(specs)
            self.assertEqual(
                (
                    "SpecDD resolve exited with status 1: "
                    "resolver failed with detail"
                ),
                error,
            )

    def test_malformed_resolver_json_becomes_unresolved_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target_path = root / "src" / "auth" / "service.ts"
            target_path.parent.mkdir(parents=True)
            target_path.touch()
            target = boundary.normalize_target(
                root,
                "src/auth/service.ts",
            )

            def runner(args, **kwargs):
                return subprocess.CompletedProcess(
                    args,
                    0,
                    "{not-json",
                    "",
                )

            specs, error = boundary.resolve_target(
                root,
                target,
                "specdd",
                runner=runner,
            )

            self.assertIsNone(specs)
            self.assertRegex(
                error,
                r"^SpecDD resolve returned malformed JSON:",
            )


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

    def test_missing_target_is_preserved_as_unresolved(self):
        schema = boundary.load_schema(REPO_ROOT)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
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
            payload["crossBoundary"],
        )
        self.assertEqual(
            1,
            len(payload["unresolved"]),
        )

        unresolved_text = json.dumps(
            payload["unresolved"][0],
            sort_keys=True,
        )
        self.assertIn(
            "src/missing.ts",
            unresolved_text,
        )
        self.assertIn(
            "does not exist",
            unresolved_text,
        )

    def test_write_boundary_supports_stdout_and_file_modes(self):
        payload = {
            "schemaVersion": 1,
        }

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
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
                        encoding="utf-8",
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
                    "src\\missing.ts",
                    "missing",
                    "src/missing.ts",
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


@unittest.skipUnless(
    shutil.which("specdd"),
    "SpecDD CLI is required for the fixture integration test",
)
class RealFixtureIntegrationTests(unittest.TestCase):
    def run_fixture(self):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--root",
                str(FIXTURE_ROOT),
                "--feature",
                "two-domain-fixture",
                "src/users/repository.ts",
                "src/auth/service.ts",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_two_domain_fixture_produces_valid_cross_boundary(self):
        if not FIXTURE_ROOT.is_dir():
            self.skipTest(
                "two-domain fixture is not available"
            )

        result = self.run_fixture()
        rerun = self.run_fixture()

        self.assertEqual(
            0,
            result.returncode,
            result.stderr,
        )
        self.assertEqual(
            0,
            rerun.returncode,
            rerun.stderr,
        )
        self.assertEqual(
            result.stdout,
            rerun.stdout,
        )

        payload = json.loads(result.stdout)
        schema = boundary.load_schema(REPO_ROOT)
        boundary.validate_boundary(
            payload,
            schema,
        )

        self.assertEqual(
            [
                "src/auth/auth.sdd",
                "src/users/users.sdd",
            ],
            payload["authorities"],
        )
        self.assertTrue(
            payload["crossBoundary"],
        )
        self.assertEqual(
            [],
            payload["unresolved"],
        )
        self.assertEqual(
            [
                "src/auth/service.ts",
                "src/users/repository.ts",
            ],
            [
                target["path"]
                for target in payload["targets"]
            ],
        )

        rendered = json.dumps(
            payload,
            sort_keys=True,
        )
        self.assertIn(
            "1.1.1",
            rendered,
        )
        self.assertIn(
            "1.5",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
