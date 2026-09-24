"""Release proof against published immutable Boundary commit archives."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TESTS = Path(__file__).resolve().parent
FIXTURE = TESTS / "fixtures" / "consumer-release"
for path in (SCRIPTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from consumer_lock import BoundaryLock, load_lock, write_lock  # noqa: E402
from consumer_test_support import (  # noqa: E402
    assert_no_boundary_generated_status,
    clone_fixture,
    run_consumer,
    run_git,
    status_paths,
)


_RELEASE_ENABLED = os.environ.get("BOUNDARY_RELEASE_ARCHIVE_TESTS") == "1"
_CANONICAL_SOURCE_DIRS = (
    "src/boundary",
    "skills",
    "adapters",
    "integration",
)


def initialize_release_fixture(
    target: Path,
    *,
    lock: BoundaryLock | None = None,
) -> None:
    if not FIXTURE.is_dir():
        raise AssertionError(
            "tests/fixtures/consumer-release is missing"
        )
    shutil.copytree(FIXTURE, target)
    for relative in _CANONICAL_SOURCE_DIRS:
        if (target / relative).exists():
            raise AssertionError(
                "release consumer fixture carries canonical Boundary source: "
                f"{relative}"
            )
    if lock is not None:
        write_lock(target / "boundary.lock.json", lock)

    run_git(target, "init", "-q")
    run_git(target, "config", "user.email", "tests@example.invalid")
    run_git(target, "config", "user.name", "Boundary Tests")
    run_git(target, "add", "-A")
    run_git(target, "commit", "-q", "-m", "real consumer fixture")


def assert_no_canonical_source(
    case: unittest.TestCase,
    root: Path,
) -> None:
    for relative in _CANONICAL_SOURCE_DIRS:
        case.assertFalse((root / relative).exists(), relative)


@unittest.skipUnless(
    _RELEASE_ENABLED,
    "set BOUNDARY_RELEASE_ARCHIVE_TESTS=1 for published archive proof",
)
class ConsumerReleaseArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        for command in ("git", "uv", "codex"):
            self.assertIsNotNone(
                shutil.which(command),
                f"release archive proof requires {command}",
            )
        for name in ("boundary.lock.json", "boundary-upgrade.lock.json"):
            self.assertTrue(
                (FIXTURE / name).is_file(),
                f"release archive fixture is missing {name}",
            )

    def test_fresh_clone_real_archive_lifecycle(self) -> None:
        initial = load_lock(FIXTURE / "boundary.lock.json")
        upgrade = load_lock(FIXTURE / "boundary-upgrade.lock.json")
        self.assertNotEqual(initial, upgrade)

        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            fixture = temp / "fixture"
            initialize_release_fixture(fixture)
            consumer = temp / "consumer"
            clone_fixture(fixture, consumer)

            self.assertEqual(0, run_consumer(consumer, "install"))
            self.assertEqual(0, run_consumer(consumer, "check"))
            assert_no_canonical_source(self, consumer)
            assert_no_boundary_generated_status(self, consumer)
            self.assertTrue(
                status_paths(consumer),
                "shared host state should remain visible to Git",
            )

            self.assertEqual(0, run_consumer(consumer, "remove"))
            assert_no_boundary_generated_status(self, consumer)
            self.assertEqual(0, run_consumer(consumer, "reinstall"))
            self.assertEqual(0, run_consumer(consumer, "check"))
            assert_no_boundary_generated_status(self, consumer)

            self.assertEqual(
                0,
                run_consumer(
                    consumer,
                    "upgrade",
                    "--source",
                    upgrade.source_url,
                    "--revision",
                    upgrade.revision,
                    "--sha256",
                    upgrade.sha256,
                ),
            )
            self.assertEqual(
                upgrade,
                load_lock(consumer / "boundary.lock.json"),
            )
            self.assertEqual(0, run_consumer(consumer, "check"))
            assert_no_boundary_generated_status(self, consumer)

            broken = BoundaryLock(
                source_url=initial.source_url,
                revision=initial.revision,
                sha256="0" * 64,
            )
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
                upgrade,
                load_lock(consumer / "boundary.lock.json"),
            )
            self.assertEqual(0, run_consumer(consumer, "check"))
            assert_no_boundary_generated_status(self, consumer)

    def test_real_archive_checksum_failure_keeps_clone_clean(self) -> None:
        initial = load_lock(FIXTURE / "boundary.lock.json")
        broken = BoundaryLock(
            source_url=initial.source_url,
            revision=initial.revision,
            sha256="0" * 64,
        )

        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            fixture = temp / "fixture"
            initialize_release_fixture(fixture, lock=broken)
            consumer = temp / "consumer"
            clone_fixture(fixture, consumer)

            self.assertEqual(2, run_consumer(consumer, "install"))
            self.assertEqual((), status_paths(consumer))
            assert_no_canonical_source(self, consumer)
            self.assertFalse(
                (consumer / ".specify" / "boundary-runtime").exists()
            )


if __name__ == "__main__":
    unittest.main()
