import tempfile
import unittest
from pathlib import Path

from boundary_test_support import boundary


class BoundaryNormalizationTests(unittest.TestCase):
    def test_discovers_specdd_root_without_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = (
                Path(temporary).resolve()
                / "repo"
            )
            nested = root / "src" / "auth"
            nested.mkdir(parents=True)

            bootstrap = (
                root
                / ".specdd"
                / "bootstrap.md"
            )
            bootstrap.parent.mkdir()
            bootstrap.write_text(
                "---\nVersion: 1.5\n---\n",
                encoding="utf-8",
            )

            self.assertEqual(
                root,
                boundary.discover_repository_root(
                    nested
                ),
            )

    def test_normalizes_repository_relative_target(self):
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
            parent = Path(
                temporary
            ).resolve()
            root = parent / "repo"
            root.mkdir()

            outside = (
                parent
                / "outside.ts"
            )
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
            root = Path(
                temporary
            ).resolve()

            self.assertEqual(
                "src/auth/auth.sdd",
                boundary.normalize_resolver_path(
                    root,
                    "src\\auth\\auth.sdd",
                    spec=True,
                ),
            )
