import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary_test_support import REPO_ROOT, boundary


def resolver_payload(specs):
    return json.dumps({"directories": [{"path": "/", "specs": specs}]})


class ResolverProjectionTests(unittest.TestCase):
    def test_extracts_compact_resolver_sections_and_derives_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "src" / "auth" / "service.ts"
            target.parent.mkdir(parents=True)
            target.touch()
            payload = {
                "directories": [
                    {
                        "path": "/",
                        "specs": [{
                            "path": "fixture.sdd",
                            "sections": {"Owns": [{"body": ["./README.md"]}]},
                        }],
                    },
                    {
                        "path": "/src/auth/",
                        "specs": [{
                            "path": "src/auth/auth.sdd",
                            "sections": {"Owns": [{"body": ["./*.ts"]}]},
                        }],
                    },
                ]
            }
            specs = boundary.extract_resolved_specs(payload, root)
            authority, owners = boundary.derive_primary_authority(
                root, "src/auth/service.ts", specs
            )

        self.assertEqual(
            ["fixture.sdd", "src/auth/auth.sdd"],
            [item["path"] for item in specs],
        )
        self.assertEqual("src/auth/auth.sdd", authority)
        self.assertEqual(["src/auth/auth.sdd"], owners)

    def test_context_fingerprint_tracks_effective_contract_drift(self):
        base = [
            {
                "path": "project.sdd",
                "sections": {
                    "Must": [{"body": ["Preserve stable behavior."]}],
                    "References": [{"body": ["./policy.sdd"]}],
                },
            },
            {
                "path": "policy.sdd",
                "sections": {"Forbids": [{"body": ["@ForbiddenDependency"]}]},
            },
        ]
        baseline = boundary.specdd_context_fingerprint(base)
        variants = []
        changed = copy.deepcopy(base)
        changed[0]["sections"]["Must"][0]["body"] = ["Preserve stricter behavior."]
        variants.append(changed)
        changed = copy.deepcopy(base)
        changed[1]["sections"]["Forbids"][0]["body"] = ["@DifferentForbiddenDependency"]
        variants.append(changed)
        changed = copy.deepcopy(base)
        changed[0]["sections"]["References"][0]["body"] = ["./other-policy.sdd"]
        variants.append(changed)
        changed = copy.deepcopy(base)
        changed[1]["sections"]["Must"] = [{"body": ["Referenced policy changed."]}]
        variants.append(changed)
        changed = copy.deepcopy(base)
        changed.append({
            "path": "local.sdd",
            "sections": {"Must": [{"body": ["Apply local behavior."]}]},
        })
        variants.append(changed)

        self.assertEqual(
            baseline,
            boundary.specdd_context_fingerprint(copy.deepcopy(base)),
        )
        for specs in variants:
            self.assertNotEqual(baseline, boundary.specdd_context_fingerprint(specs))

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

    def test_missing_target_kind_flags_are_forwarded_to_resolver(self):
        cases = (
            ("src/new.ts", "--file"),
            ("src/new-domain/", "--folder"),
            ("src/new-service.sdd", "--sdd-file"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for raw, expected_flag in cases:
                with self.subTest(raw=raw):
                    calls = []

                    def runner(args, **kwargs):
                        calls.append(args)
                        return subprocess.CompletedProcess(
                            args, 0,
                            resolver_payload([{"path": "project.sdd", "sections": {}}]),
                            "",
                        )

                    specs, error = boundary.resolve_target(
                        root,
                        boundary.normalize_target(root, raw),
                        "specdd",
                        runner=runner,
                    )
                    self.assertIsNone(error)
                    self.assertIsNotNone(specs)
                    self.assertIn(expected_flag, calls[0])

            existing = root / "src" / "existing.ts"
            existing.parent.mkdir(parents=True, exist_ok=True)
            existing.touch()
            calls = []

            def existing_runner(args, **kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(
                    args, 0,
                    resolver_payload([{"path": "project.sdd", "sections": {}}]), ""
                )

            boundary.resolve_target(
                root, boundary.normalize_target(root, "src/existing.ts"),
                "specdd", runner=existing_runner,
            )
            self.assertFalse({"--file", "--folder", "--sdd-file"} & set(calls[0]))

    def test_capable_pinned_resolver_projects_intended_owner_shapes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "src" / "owned").mkdir(parents=True)
            specs = [
                {
                    "path": "src/owner.sdd",
                    "sections": {"Owns": [{"body": [
                        "./exact.ts",
                        "./owned",
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
                self.assertIn("--file", args)
                return subprocess.CompletedProcess(args, 0, resolver_payload(specs), "")

            payload = boundary.build_change_boundary(
                root,
                (
                    "src/exact.ts",
                    "src/owned/new.ts",
                    "src/generated/new.ts",
                    "src/ambiguous.ts",
                    "src/no-owner.ts",
                ),
                feature="sample",
                schema=boundary.load_schema(REPO_ROOT),
                runner=runner,
                cli_version="1.2.0",
                specdd_framework_version="1.5",
                intended_targets_supported=True,
            )

        self.assertEqual(
            {"src/exact.ts", "src/owned/new.ts", "src/generated/new.ts"},
            {item["path"] for item in payload["targets"]},
        )
        records = {item["normalizedPath"]: item for item in payload["unresolved"]}
        self.assertEqual("AMBIGUOUS_AUTHORITY", records["src/ambiguous.ts"]["code"])
        self.assertEqual("UNRESOLVED_TARGET", records["src/no-owner.ts"]["code"])

    def test_resolver_failures_are_normalized(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target_path = root / "src" / "auth" / "service.ts"
            target_path.parent.mkdir(parents=True)
            target_path.touch()
            target = boundary.normalize_target(root, "src/auth/service.ts")

            def failed(args, **kwargs):
                return subprocess.CompletedProcess(args, 1, "", "resolver failed\nwith detail")

            specs, error = boundary.resolve_target(root, target, "specdd", runner=failed)
            self.assertIsNone(specs)
            self.assertEqual(
                "SpecDD resolve exited with status 1: resolver failed with detail",
                error,
            )

            def malformed(args, **kwargs):
                return subprocess.CompletedProcess(args, 0, "{not-json", "")

            specs, error = boundary.resolve_target(
                root, target, "specdd", runner=malformed
            )
            self.assertIsNone(specs)
            self.assertRegex(error, r"^SpecDD resolve returned malformed JSON:")
