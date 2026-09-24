"""Tests for immutable downstream Boundary source locks."""

from __future__ import annotations

from pathlib import Path
from unittest import mock
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import consumer as consumer_module  # noqa: E402
from consumer_lock import (  # noqa: E402
    BoundaryLock,
    BoundaryLockError,
    load_lock,
    write_lock,
)


class BoundaryLockTests(unittest.TestCase):
    def test_round_trips_exact_immutable_source_identity(self) -> None:
        revision = "a" * 40
        lock = BoundaryLock(
            source_url=(
                "https://github.com/example/boundary/archive/"
                f"{revision}.tar.gz"
            ),
            revision=revision,
            sha256="b" * 64,
        )

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "boundary.lock.json"
            write_lock(path, lock)

            loaded = load_lock(path)

        self.assertEqual(loaded, lock)
        self.assertEqual(loaded.to_document(), lock.to_document())

    def test_locked_install_passes_materialized_source(self) -> None:
        revision = "a" * 40
        lock = BoundaryLock(
            source_url=(
                "https://github.com/example/boundary/archive/"
                f"{revision}.tar.gz"
            ),
            revision=revision,
            sha256="b" * 64,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "consumer"
            source = Path(temp) / "source"
            root.mkdir()
            source.mkdir()
            with (
                mock.patch.object(
                    consumer_module,
                    "materialize_locked_source",
                    return_value=source,
                ),
                mock.patch.object(
                    consumer_module.subprocess,
                    "run",
                    return_value=mock.Mock(returncode=0),
                ) as run,
            ):
                consumer_module._with_source(root, lock, "install")

        command = run.call_args.args[0]
        self.assertEqual(
            command[-2:],
            ["--source", str(source)],
        )

    def test_rejects_mutable_tag_archive(self) -> None:
        with self.assertRaisesRegex(
            BoundaryLockError,
            "immutable HTTPS GitHub commit archive",
        ):
            BoundaryLock(
                source_url=(
                    "https://github.com/example/boundary/archive/"
                    "refs/tags/v1.0.0.tar.gz"
                ),
                revision="a" * 40,
                sha256="b" * 64,
            )

    def test_rejects_revision_that_disagrees_with_url(self) -> None:
        with self.assertRaisesRegex(
            BoundaryLockError,
            "url revision does not match",
        ):
            BoundaryLock(
                source_url=(
                    "https://github.com/example/boundary/archive/"
                    f"{'a' * 40}.zip"
                ),
                revision="c" * 40,
                sha256="b" * 64,
            )

    def test_rejects_unknown_source_fields(self) -> None:
        revision = "a" * 40
        document = {
            "schema": "boundary.lock/v1",
            "source": {
                "url": (
                    "https://github.com/example/boundary/archive/"
                    f"{revision}.zip"
                ),
                "revision": revision,
                "sha256": "b" * 64,
                "branch": "main",
            },
        }

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "boundary.lock.json"
            path.write_text(
                json.dumps(document),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BoundaryLockError,
                "url, revision, and sha256",
            ):
                load_lock(path)


if __name__ == "__main__":
    unittest.main()
