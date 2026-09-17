import os
import tempfile
import unittest
from pathlib import Path

from boundary_runtime import normalize_command_output
from boundary_test_support import boundary


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

            self.assertEqual("src/auth/service.ts", result.path)
            self.assertEqual(target, result.absolute_path)

    def test_preserves_spaces_and_literal_grouping_characters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "src" / "auth" / "provider [legacy].ts"
            target.parent.mkdir(parents=True)
            target.touch()

            result = boundary.normalize_target(
                root,
                "src\\auth\\provider [legacy].ts",
            )

            self.assertEqual(
                "src/auth/provider [legacy].ts",
                result.path,
            )
            self.assertEqual(target, result.absolute_path)

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
                boundary.normalize_target(root, str(outside))

    def test_rejects_foreign_absolute_path_style(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            foreign = (
                "/tmp/specdd-foreign/src/auth/auth.sdd"
                if os.name == "nt"
                else r"C:\specdd-foreign\src\auth\auth.sdd"
            )
            style = "POSIX" if os.name == "nt" else "Windows"

            with self.assertRaisesRegex(
                boundary.BoundaryError,
                f"absolute {style} path on this host",
            ):
                boundary.normalize_target(root, foreign)

            with self.assertRaisesRegex(
                boundary.BoundaryError,
                f"absolute {style} path on this host",
            ):
                boundary.normalize_resolver_path(
                    root,
                    foreign,
                    spec=True,
                )

    def test_normalizes_command_output_root_and_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            output = (
                f"failed at {root.as_posix()}/src/auth/auth.sdd\r\n"
                "with detail\r"
            )

            self.assertEqual(
                "failed at ./src/auth/auth.sdd\nwith detail",
                normalize_command_output(root, output),
            )

    @unittest.skipUnless(
        os.name == "nt",
        "Drive-qualified path evidence requires Windows",
    )
    def test_accepts_drive_qualified_absolute_paths_inside_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "src" / "auth" / "service.ts"
            target.parent.mkdir(parents=True)
            target.touch()
            spec = root / "src" / "auth" / "auth.sdd"

            for raw in (str(target), target.as_posix()):
                with self.subTest(raw=raw):
                    result = boundary.normalize_target(root, raw)
                    self.assertEqual("src/auth/service.ts", result.path)

            for raw in (str(spec), spec.as_posix()):
                with self.subTest(resolver_raw=raw):
                    self.assertEqual(
                        "src/auth/auth.sdd",
                        boundary.normalize_resolver_path(
                            root,
                            raw,
                            spec=True,
                        ),
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
