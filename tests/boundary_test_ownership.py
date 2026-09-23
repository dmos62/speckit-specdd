import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary_test_support import REPO_ROOT, boundary, resolver_payload


class OwnershipProjectionTests(unittest.TestCase):
    def test_specdd_globstar_matches_nested_targets(self):
        self.assertTrue(boundary._glob_matches("src/auth/**", "src/auth/deep/service.ts"))
        self.assertTrue(
            boundary._glob_matches("src/auth/**/*", "src/auth/deep/nested/service.ts")
        )
        self.assertTrue(
            boundary._glob_matches("src/**/service.{ts,js}", "src/auth/deep/service.ts")
        )
        self.assertFalse(
            boundary._glob_matches("src/auth/*.ts", "src/auth/deep/service.ts")
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
                    "sections": {"Owns": [{"body": ["./src/auth"]}]},
                },
                {
                    "path": "src/auth/auth.sdd",
                    "sections": {"Owns": [{"body": ["./service.ts"]}]},
                },
            ]
            authority, owners = boundary.derive_primary_authority(
                root, "src/auth/service.ts", specs
            )

        self.assertIsNone(authority)
        self.assertEqual(["root.sdd", "src/auth/auth.sdd"], owners)

    def test_intended_owner_shapes_and_creation_parity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "src" / "owned").mkdir(parents=True)
            specs = [
                {
                    "path": "src/owner.sdd",
                    "sections": {"Owns": [{"body": [
                        "./exact.ts",
                        "./owned",
                        "./future-domain",
                        "./generated/*.ts",
                        "./ambiguous.ts",
                    ]}]},
                },
                {
                    "path": "src/other.sdd",
                    "sections": {"Owns": [{"body": ["./ambiguous.ts"]}]},
                },
            ]

            def runner(args, **kwargs):
                return subprocess.CompletedProcess(
                    args, 0, resolver_payload(specs), ""
                )

            paths = (
                "src/exact.ts",
                "src/owned/new.ts",
                "src/future-domain/new.ts",
                "src/generated/new.ts",
                "src/ambiguous.ts",
                "src/no-owner.ts",
            )
            intended = self._build(root, paths, runner)

            parity_paths = (
                "src/exact.ts",
                "src/owned/new.ts",
                "src/generated/new.ts",
            )
            for path in parity_paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
            created = self._build(root, parity_paths, runner)

            future_target = root / "src" / "future-domain" / "new.ts"
            future_target.parent.mkdir(parents=True)
            future_target.touch()
            known_directory = self._build(
                root, ("src/future-domain/new.ts",), runner
            )

        self.assertEqual(
            {"src/exact.ts", "src/owned/new.ts", "src/generated/new.ts"},
            {item["path"] for item in intended["targets"]},
        )
        unresolved = {
            item["normalizedPath"]: item
            for item in intended["unresolved"]
        }
        self.assertEqual(
            "UNRESOLVED_TARGET",
            unresolved["src/future-domain/new.ts"]["code"],
        )
        self.assertEqual(
            "AMBIGUOUS_AUTHORITY",
            unresolved["src/ambiguous.ts"]["code"],
        )
        self.assertEqual(
            "UNRESOLVED_TARGET",
            unresolved["src/no-owner.ts"]["code"],
        )

        intended_authorities = {
            item["path"]: item["primaryAuthority"]
            for item in intended["targets"]
            if item["path"] in parity_paths
        }
        created_authorities = {
            item["path"]: item["primaryAuthority"]
            for item in created["targets"]
        }
        self.assertEqual(intended_authorities, created_authorities)
        self.assertEqual(
            [("src/future-domain/new.ts", "src/owner.sdd")],
            [
                (item["path"], item["primaryAuthority"])
                for item in known_directory["targets"]
            ],
        )

    @staticmethod
    def _build(root, paths, runner):
        return boundary.build_change_boundary(
            root,
            paths,
            feature="sample",
            schema=boundary.load_schema(REPO_ROOT),
            runner=runner,
            cli_version="1.2.0",
            specdd_framework_version="1.5",
            intended_targets_supported=True,
        )
