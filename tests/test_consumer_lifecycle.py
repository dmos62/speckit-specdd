"""Consumer lifecycle coverage using checksum-verified archive bytes."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
from unittest import mock
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TESTS = Path(__file__).resolve().parent
for path in (SCRIPTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import consumer_lock as lock_module  # noqa: E402
from consumer_lock import BoundaryLock, load_lock  # noqa: E402
from consumer_test_support import (  # noqa: E402
    assert_no_boundary_generated_status,
    clone_fixture,
    download_from,
    initialize_fixture,
    make_archive,
    run_consumer,
    status_paths,
)


@unittest.skipUnless(shutil.which("git"), "Git is required")
class ConsumerArchiveLifecycleTests(unittest.TestCase):
    def test_fresh_clone_lifecycle_and_deliberate_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            v1, archive1 = make_archive(temp, "1" * 40, "v1")
            v2, archive2 = make_archive(temp, "2" * 40, "v2")
            fixture = temp / "fixture"
            fixture.mkdir()
            initialize_fixture(fixture, v1)
            consumer = temp / "consumer"
            clone_fixture(fixture, consumer)

            archives = {
                v1.source_url: archive1,
                v2.source_url: archive2,
            }
            with mock.patch.object(
                lock_module,
                "_download",
                side_effect=download_from(archives),
            ):
                self.assertEqual(0, run_consumer(consumer, "install"))
                self.assertEqual(0, run_consumer(consumer, "check"))
                for path in (
                    "src/boundary",
                    "skills",
                    "adapters",
                    "integration",
                ):
                    self.assertFalse((consumer / path).exists())
                assert_no_boundary_generated_status(self, consumer)
                self.assertEqual(
                    (".specify/shared-registry.json",),
                    status_paths(consumer),
                )

                self.assertEqual(0, run_consumer(consumer, "remove"))
                self.assertEqual((), status_paths(consumer))
                self.assertEqual(0, run_consumer(consumer, "reinstall"))
                self.assertEqual(0, run_consumer(consumer, "check"))
                assert_no_boundary_generated_status(self, consumer)

                self.assertEqual(
                    0,
                    run_consumer(
                        consumer,
                        "upgrade",
                        "--source",
                        v2.source_url,
                        "--revision",
                        v2.revision,
                        "--sha256",
                        v2.sha256,
                    ),
                )
                self.assertEqual(
                    v2,
                    load_lock(consumer / "boundary.lock.json"),
                )
                self.assertEqual(0, run_consumer(consumer, "check"))
                assert_no_boundary_generated_status(self, consumer)

    def test_checksum_failure_leaves_fresh_clone_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            good, archive = make_archive(temp, "3" * 40, "v1")
            bad = BoundaryLock(
                source_url=good.source_url,
                revision=good.revision,
                sha256="0" * 64,
            )
            fixture = temp / "fixture"
            fixture.mkdir()
            initialize_fixture(fixture, bad)
            consumer = temp / "consumer"
            clone_fixture(fixture, consumer)

            with mock.patch.object(
                lock_module,
                "_download",
                side_effect=download_from({good.source_url: archive}),
            ):
                self.assertEqual(2, run_consumer(consumer, "install"))

            self.assertEqual((), status_paths(consumer))
            self.assertFalse((consumer / ".agents").exists())
            self.assertFalse(
                (consumer / ".specify" / "boundary-runtime").exists()
            )

    def test_failed_upgrade_restores_previous_locked_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            v1, archive1 = make_archive(temp, "4" * 40, "v1")
            broken, archive2 = make_archive(
                temp,
                "5" * 40,
                "broken",
                fail_install=True,
            )
            fixture = temp / "fixture"
            fixture.mkdir()
            initialize_fixture(fixture, v1)
            consumer = temp / "consumer"
            clone_fixture(fixture, consumer)
            archives = {
                v1.source_url: archive1,
                broken.source_url: archive2,
            }

            with mock.patch.object(
                lock_module,
                "_download",
                side_effect=download_from(archives),
            ):
                self.assertEqual(0, run_consumer(consumer, "install"))
                self.assertEqual(
                    2,
                    run_consumer(
                        consumer,
                        "upgrade",
                        "--source",
                        broken.source_url,
                        "--revision",
                        broken.revision,
                        "--sha256",
                        broken.sha256,
                    ),
                )
                self.assertEqual(
                    v1,
                    load_lock(consumer / "boundary.lock.json"),
                )
                self.assertEqual(0, run_consumer(consumer, "check"))

            installed = (
                consumer
                / ".specify"
                / "boundary-runtime"
                / "installed-version"
            )
            self.assertEqual(
                "v1\n",
                installed.read_text(encoding="utf-8"),
            )
            assert_no_boundary_generated_status(self, consumer)


if __name__ == "__main__":
    unittest.main()
