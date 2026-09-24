import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

SKILLS = {
    "boundary-scope": REPO_ROOT / "skills" / "scope" / "SKILL.md",
    "boundary-implement": REPO_ROOT / "skills" / "implement" / "SKILL.md",
    "boundary-contracts": REPO_ROOT / "skills" / "contracts" / "SKILL.md",
}


class CanonicalBoundarySkillTests(unittest.TestCase):
    def _content(self, name: str) -> str:
        return SKILLS[name].read_text(encoding="utf-8")

    def test_canonical_skills_are_small_plain_markdown(self):
        for name, path in SKILLS.items():
            with self.subTest(skill=name):
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith(f"# {name}\n"))
                self.assertLessEqual(len(content.splitlines()), 250)
                self.assertFalse(content.startswith("---\n"))

    def test_canonical_skills_exclude_vendor_and_transient_state(self):
        forbidden = (
            ".agents/",
            ".specdd/",
            "Spec Kit",
            "SpecDD",
            "Codex",
            "Claude",
            "SPECDD_AUTHORITY",
            "boundary.json",
            "authorizationSnapshot",
        )
        version_pattern = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b")
        hash_pattern = re.compile(r"\b[0-9a-fA-F]{40,64}\b")

        for name in SKILLS:
            with self.subTest(skill=name):
                content = self._content(name)
                for marker in forbidden:
                    self.assertNotIn(marker, content)
                self.assertIsNone(version_pattern.search(content))
                self.assertIsNone(hash_pattern.search(content))

    def test_scope_skill_keeps_planning_separate_from_authorization(self):
        content = self._content("boundary-scope")

        for marker in (
            "exact repository-relative targets",
            "effective context",
            "additively",
            "structured write declaration",
            "Path-looking prose",
            "Do not authorize implementation from this skill",
            "Authorization remains a separate deterministic transition",
        ):
            self.assertIn(marker, content)

    def test_implementation_skill_requires_explicit_scope_expansion(self):
        content = self._content("boundary-implement")

        for marker in (
            "authorized write set",
            "Do not write the undeclared target",
            "fresh implementation authorization",
            "persistent-contract evolution",
            "Native contract files are not implementation targets",
            "Boundary verification",
        ):
            self.assertIn(marker, content)

    def test_contract_skill_enforces_operation_separation(self):
        content = self._content("boundary-contracts")

        for marker in (
            "persistent Boundary contracts",
            "additive applicability",
            "Modify only native contract files",
            "structural contract check",
            "fresh implementation authorization",
            "never retroactively authorizes implementation writes",
        ):
            self.assertIn(marker, content)


if __name__ == "__main__":
    unittest.main()
