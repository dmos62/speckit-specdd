import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary_test_support import boundary


class ResolverProjectionTests(unittest.TestCase):
    def test_extracts_compact_resolver_sections_and_derives_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            service = (
                root
                / "src"
                / "auth"
                / "service.ts"
            )
            service.parent.mkdir(
                parents=True
            )
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
            authority, owners = (
                boundary.derive_primary_authority(
                    root,
                    "src/auth/service.ts",
                    specs,
                )
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
            target = (
                root
                / "src"
                / "auth"
                / "service.ts"
            )
            target.parent.mkdir(
                parents=True
            )
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

            authority, owners = (
                boundary.derive_primary_authority(
                    root,
                    "src/auth/service.ts",
                    specs,
                )
            )

            self.assertIsNone(
                authority
            )
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
            target_path = (
                root
                / "src"
                / "auth"
                / "service.ts"
            )
            target_path.parent.mkdir(
                parents=True
            )
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

            self.assertIsNone(
                specs
            )
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
            target_path = (
                root
                / "src"
                / "auth"
                / "service.ts"
            )
            target_path.parent.mkdir(
                parents=True
            )
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

            self.assertIsNone(
                specs
            )
            self.assertRegex(
                error,
                (
                    r"^SpecDD resolve returned "
                    r"malformed JSON:"
                ),
            )
