import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIMES = {
    "codex": (
        REPO_ROOT / "adapters" / "codex" / "materialize.py",
        Path(".agents") / "skills",
    ),
    "claude": (
        REPO_ROOT / "adapters" / "claude" / "materialize.py",
        Path(".claude") / "skills",
    ),
}
SKILLS = {
    "boundary-scope": "scope",
    "boundary-implement": "implement",
    "boundary-contracts": "contracts",
}


class AgentSkillMaterializationTests(unittest.TestCase):
    def _run(
        self,
        runtime: str,
        project_root: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        adapter, _ = RUNTIMES[runtime]
        return subprocess.run(
            [
                sys.executable,
                str(adapter),
                "--source-root",
                str(REPO_ROOT),
                "--project-root",
                str(project_root),
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def _assert_materialized(
        self,
        runtime: str,
        project_root: Path,
    ) -> None:
        _, target_root = RUNTIMES[runtime]
        for skill_name, source_name in SKILLS.items():
            with self.subTest(runtime=runtime, skill=skill_name):
                target = (
                    project_root
                    / target_root
                    / skill_name
                    / "SKILL.md"
                )
                content = target.read_text(encoding="utf-8")
                header, body = content[len("---\n") :].split(
                    "\n---\n\n",
                    1,
                )
                self.assertTrue(content.startswith("---\n"))
                self.assertIn(f"name: {skill_name}", header)
                self.assertIn("description:", header)

                canonical = (
                    REPO_ROOT
                    / "skills"
                    / source_name
                    / "SKILL.md"
                ).read_text(encoding="utf-8")
                if not canonical.endswith("\n"):
                    canonical += "\n"
                self.assertEqual(canonical, body)

    def test_concrete_runtime_adapters_materialize_discoverable_skills(
        self,
    ):
        for runtime in RUNTIMES:
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    result = self._run(runtime, root)
                    self.assertEqual(
                        0,
                        result.returncode,
                        result.stderr,
                    )
                    self._assert_materialized(runtime, root)

                    checked = self._run(runtime, root, "--check")
                    self.assertEqual(
                        0,
                        checked.returncode,
                        checked.stderr,
                    )

    def test_codex_skill_bytes_ignore_unrelated_feature_operations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self._run("codex", root)
            self.assertEqual(0, first.returncode, first.stderr)

            skill_root = root / RUNTIMES["codex"][1]
            before = {
                name: (skill_root / name / "SKILL.md").read_bytes()
                for name in SKILLS
            }

            operation = (
                root
                / "specs"
                / "001-unrelated"
                / "operation.json"
            )
            operation.parent.mkdir(parents=True)
            operation.write_text(
                '{"operation":"different"}\n',
                encoding="utf-8",
            )

            second = self._run("codex", root)
            self.assertEqual(0, second.returncode, second.stderr)
            after = {
                name: (skill_root / name / "SKILL.md").read_bytes()
                for name in SKILLS
            }
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
