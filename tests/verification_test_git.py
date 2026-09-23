import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from boundary_test_support import verification


class VerificationGitTests(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def initialize_repository(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name).resolve()
        self.git(root, "init")
        self.git(root, "config", "user.name", "SpecDD Test")
        self.git(root, "config", "user.email", "specdd@example.test")
        files = {
            "src/auth/service.ts": "export const value = 1;\n",
            ".specify/generated.json": "{}\n",
            ".specdd/bootstrap.project.md": "# Project\n",
            ".specdd/bootstrap.local.md": "# Local\n",
            "specs/001-login/spec.md": "# Feature\n",
            "docs/old.md": "old\n",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "-c", "commit.gpgsign=false", "commit", "-m", "baseline")
        return temporary, root

    def authorization_boundary(self):
        return {"schemaVersion": 1, "feature": "001-login"}

    def write_and_load_baseline(self, root):
        boundary = self.authorization_boundary()
        snapshot, plan = verification.write_authorization_evidence(root, boundary, ())
        baseline_path = verification.authorization_git_baseline_path(root)
        baseline = verification.load_authorization_git_baseline(
            root, baseline_path, boundary
        )
        return boundary, snapshot, plan, baseline_path, baseline

    def test_separates_actual_writes_from_nonimplementation_state(self):
        temporary, root = self.initialize_repository()
        with temporary:
            (root / "src/auth/service.ts").write_text("export const value = 2;\n", encoding="utf-8")
            (root / ".specify/generated.json").write_text('{"changed": true}\n', encoding="utf-8")
            (root / "specs/001-login/spec.md").write_text("# Changed feature\n", encoding="utf-8")
            (root / ".specdd/bootstrap.project.md").write_text("# Changed project\n", encoding="utf-8")
            (root / ".specdd/bootstrap.local.md").write_text("# Changed local\n", encoding="utf-8")
            new_write = root / "src/users/repository.ts"
            new_write.parent.mkdir(parents=True, exist_ok=True)
            new_write.write_text("export const repository = true;\n", encoding="utf-8")
            (root / "src/auth/auth.sdd").write_text("Spec: Auth\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login")

        self.assertEqual(["src/auth/service.ts", "src/users/repository.ts"], [item.path for item in changes.writes])
        self.assertEqual(["src/auth/auth.sdd"], [item.path for item in changes.specs])
        self.assertEqual([".specdd/bootstrap.project.md"], [item.path for item in changes.controls])
        self.assertEqual(["specs/001-login/spec.md"], [item.path for item in changes.feature_artifacts])
        self.assertEqual([".specdd/bootstrap.local.md", ".specify/generated.json"], [item.path for item in changes.generated])

    def test_generated_codex_skills_are_excluded_but_canonical_source_is_write(self):
        temporary, root = self.initialize_repository()
        with temporary:
            generated = root / ".agents/skills/speckit-specdd-context/SKILL.md"
            canonical = root / "integration/specdd/commands/context.md"
            for path in (generated, canonical):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Changed\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login")
        self.assertIn(".agents/skills/speckit-specdd-context/SKILL.md", [item.path for item in changes.generated])
        self.assertIn("integration/specdd/commands/context.md", [item.path for item in changes.writes])

    def test_authorization_evidence_preserves_boundary_plans_and_git_baseline(self):
        temporary, root = self.initialize_repository()
        with temporary:
            payload = self.authorization_boundary()
            specs = ("src/auth/auth.sdd", "src/users/users.sdd")
            controls = {
                ".specdd/bootstrap.project.md": "workflow",
                ".specdd/bootstrap.local.md": "operator",
            }
            snapshot, plan = verification.write_authorization_evidence(
                root, payload, specs, control_selections=controls
            )
            baseline = verification.authorization_git_baseline_path(root)
            self.assertEqual((root / ".git/specdd/authorization-boundary.json").resolve(), snapshot)
            self.assertEqual((root / ".git/specdd/authorization-spec-evolution.json").resolve(), plan)
            self.assertEqual((root / ".git/specdd/authorization-git-baseline.json").resolve(), baseline)
            self.assertEqual(payload, json.loads(snapshot.read_text(encoding="utf-8")))
            loaded_specs, loaded_controls = verification.load_authorization_plan(root, plan, payload)
            loaded_baseline = verification.load_authorization_git_baseline(root, baseline, payload)
            self.assertEqual(specs, loaded_specs)
            self.assertEqual(controls, loaded_controls)
            self.assertEqual({}, loaded_baseline["entries"])
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=loaded_baseline)

        self.assertEqual((), changes.writes)
        self.assertEqual((), changes.preauthorization)

    def test_clean_baseline_includes_post_authorization_write(self):
        temporary, root = self.initialize_repository()
        with temporary:
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            (root / "src/auth/service.ts").write_text("operation change\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

        self.assertEqual(["src/auth/service.ts"], [item.path for item in changes.writes])
        self.assertEqual((), changes.preauthorization)

    def test_baseline_excludes_preexisting_tracked_staged_untracked_and_deleted_state(self):
        temporary, root = self.initialize_repository()
        with temporary:
            (root / "src/auth/service.ts").write_text("preexisting tracked\n", encoding="utf-8")
            (root / "docs/old.md").write_text("preexisting staged\n", encoding="utf-8")
            self.git(root, "add", "docs/old.md")
            untracked = root / "scratch/preexisting.txt"
            untracked.parent.mkdir(parents=True, exist_ok=True)
            untracked.write_text("preexisting untracked\n", encoding="utf-8")
            (root / ".specdd/bootstrap.project.md").unlink()
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

        self.assertEqual((), changes.writes)
        self.assertEqual((), changes.controls)
        self.assertEqual(
            [
                ".specdd/bootstrap.project.md",
                "docs/old.md",
                "scratch/preexisting.txt",
                "src/auth/service.ts",
            ],
            [item.path for item in changes.preauthorization],
        )

    def test_baseline_keeps_only_post_authorization_delta_for_dirty_worktree(self):
        temporary, root = self.initialize_repository()
        with temporary:
            (root / "docs/old.md").write_text("preexisting unrelated\n", encoding="utf-8")
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            (root / "src/auth/service.ts").write_text("operation change\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

        self.assertEqual(["src/auth/service.ts"], [item.path for item in changes.writes])
        self.assertEqual(["docs/old.md"], [item.path for item in changes.preauthorization])

    def test_preexisting_dirty_path_changed_after_authorization_is_included(self):
        temporary, root = self.initialize_repository()
        with temporary:
            path = root / "src/auth/service.ts"
            path.write_text("preexisting change\n", encoding="utf-8")
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            path.write_text("operation changed same path\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

        self.assertEqual(["src/auth/service.ts"], [item.path for item in changes.writes])
        self.assertEqual((), changes.preauthorization)

    def test_preexisting_untracked_file_deleted_after_authorization_is_included(self):
        temporary, root = self.initialize_repository()
        with temporary:
            path = root / "scratch/preexisting.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("preexisting untracked\n", encoding="utf-8")
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            path.unlink()
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

        self.assertEqual(["scratch/preexisting.txt"], [item.path for item in changes.writes])
        self.assertTrue(changes.writes[0].deleted)

    def test_post_authorization_concurrent_change_remains_in_operation_scope(self):
        temporary, root = self.initialize_repository()
        with temporary:
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            (root / "src/auth/service.ts").write_text("feature change\n", encoding="utf-8")
            (root / "docs/old.md").write_text("concurrent change\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

        self.assertEqual(["docs/old.md", "src/auth/service.ts"], [item.path for item in changes.writes])
        self.assertEqual((), changes.preauthorization)

    def test_head_change_after_authorization_fails_closed(self):
        temporary, root = self.initialize_repository()
        with temporary:
            _, _, _, _, baseline = self.write_and_load_baseline(root)
            (root / "docs/old.md").write_text("committed later\n", encoding="utf-8")
            self.git(root, "add", "docs/old.md")
            self.git(root, "-c", "commit.gpgsign=false", "commit", "-m", "concurrent")
            with self.assertRaisesRegex(verification.VerificationError, "Git HEAD changed after authorization"):
                verification.collect_git_changes(root, feature_dir="specs/001-login", baseline=baseline)

    def test_spec_plan_is_bound_to_exact_authorization_snapshot(self):
        temporary, root = self.initialize_repository()
        with temporary:
            payload = self.authorization_boundary()
            _, plan = verification.write_authorization_evidence(root, payload, ("src/auth/auth.sdd",))
            with self.assertRaisesRegex(verification.VerificationError, "does not match"):
                verification.load_authorization_plan(root, plan, {**payload, "feature": "002-other"})

    def test_invalid_control_selection_is_rejected_from_evidence(self):
        temporary, root = self.initialize_repository()
        with temporary:
            payload = self.authorization_boundary()
            _, plan = verification.write_authorization_evidence(
                root, payload, (), control_selections={".specdd/bootstrap.md": "operator"}
            )
            with self.assertRaisesRegex(verification.VerificationError, "not editable"):
                verification.load_authorization_plan(root, plan, payload)

    def test_preserves_spaces_and_literal_grouping_characters_in_git_paths(self):
        temporary, root = self.initialize_repository()
        with temporary:
            special = root / "src/auth/provider [legacy].ts"
            special.write_text("export const provider = true;\n", encoding="utf-8")
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login")
        matching = [item for item in changes.writes if item.path == "src/auth/provider [legacy].ts"]
        self.assertEqual(1, len(matching))
        self.assertEqual("UNTRACKED", matching[0].status)
        self.assertFalse(matching[0].deleted)

    def test_marks_deleted_project_file(self):
        temporary, root = self.initialize_repository()
        with temporary:
            (root / "docs/old.md").unlink()
            changes = verification.collect_git_changes(root, feature_dir="specs/001-login")
        deleted = [item for item in changes.writes if item.path == "docs/old.md"]
        self.assertEqual(1, len(deleted))
        self.assertTrue(deleted[0].deleted)
        self.assertEqual("DELETED", deleted[0].status)

    def test_missing_git_is_explicit_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            def missing_git(*args, **kwargs):
                raise FileNotFoundError("git")

            with self.assertRaisesRegex(verification.VerificationError, "Required Git executable was not found") as raised:
                verification.collect_git_changes(Path(temporary).resolve(), runner=missing_git)
        self.assertTrue("Install Git before verification" in str(raised.exception) and "scripts/bootstrap.sh" not in str(raised.exception))
