import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
SCRIPT_ROOT = REPOSITORY_ROOT / "integration" / "specdd" / "scripts"
for path in (SCRIPT_ROOT, SOURCE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from spec_kit_adapter import (
    SpecKitAdapterError,
    authorize_feature,
    parse_tasks,
    verify_feature,
)


def run_git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)


def write_contract(root: Path) -> None:
    path = root / "contracts" / "app.contract.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\n"
        "schema: boundary.contract/v1\n"
        "id: app\n"
        "owns:\n"
        "  - src/**\n"
        "applies_to: []\n"
        "depends_on: []\n"
        "---\n"
        "## Invariants\n\n"
        "- Application behavior remains explicit.\n",
        encoding="utf-8",
    )


class SpecKitProjectionTests(unittest.TestCase):
    def test_projects_only_dedicated_writes_metadata(self):
        tasks = parse_tasks(
            "# Tasks\n\n"
            "- [ ] T001 [US1] Mention `docs/advisory.md` in prose\n"
            "  Writes: `src/a.py` `src/b.py`\n"
            "- [ ] T002 [P] [US2] No implementation write yet\n"
        )

        self.assertEqual(("T001", "T002"), tuple(t.task_id for t in tasks))
        self.assertEqual(("US1", "US2"), tuple(t.story for t in tasks))
        self.assertEqual(
            ("src/a.py", "src/b.py"),
            tasks[0].writes,
        )
        self.assertEqual((), tasks[1].writes)

    def test_rejects_duplicate_writes_metadata(self):
        with self.assertRaisesRegex(
            SpecKitAdapterError,
            "duplicate Writes metadata",
        ):
            parse_tasks(
                "- [ ] T001 Work\n"
                "  Writes: `src/a.py`\n"
                "  Writes: `src/b.py`\n"
            )


@unittest.skipUnless(shutil.which("git"), "Git is required")
class SpecKitLifecycleTests(unittest.TestCase):
    def initialize(self, root: Path) -> Path:
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "tests@example.invalid")
        run_git(root, "config", "user.name", "Boundary Tests")
        write_contract(root)

        source = root / "src"
        source.mkdir()
        (source / "a.py").write_text(
            "VALUE = 'before'\n",
            encoding="utf-8",
        )

        feature = root / "specs" / "001-change"
        feature.mkdir(parents=True)
        (feature / "tasks.md").write_text(
            "# Tasks\n\n"
            "- [ ] T001 [US1] Change application\n"
            "  Writes: `src/a.py`\n",
            encoding="utf-8",
        )

        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "baseline")
        return feature

    def test_authorizes_structured_scope_and_excludes_feature_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = self.initialize(root)

            authorized = authorize_feature(root, feature)
            self.assertEqual("001-change", authorized.change_id)
            self.assertEqual(
                ("src/a.py",),
                tuple(
                    target.path
                    for target in authorized.authorized_targets
                ),
            )

            (root / "src" / "a.py").write_text(
                "VALUE = 'after'\n",
                encoding="utf-8",
            )
            (feature / "progress.md").write_text(
                "host state\n",
                encoding="utf-8",
            )

            verified = verify_feature(root, feature)

        self.assertEqual("verified", verified.status)
