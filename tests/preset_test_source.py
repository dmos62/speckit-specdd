import unittest

from preset_test_support import (
    BOOTSTRAP_PATH,
    EXTENSION_ROOT,
    PRESET_ROOT,
)


class PresetSourceTests(unittest.TestCase):
    def test_manifest_uses_pinned_append_composition(self):
        manifest = (PRESET_ROOT / "preset.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'id: "specdd-bridge"',
            manifest,
        )
        self.assertIn(
            'speckit_version: "==1.0.7"',
            manifest,
        )
        self.assertIn(
            'id: specdd',
            manifest,
        )
        self.assertIn(
            'version: "==0.1.0"',
            manifest,
        )
        self.assertEqual(
            3,
            manifest.count('strategy: "append"'),
        )
        for command in (
            "speckit.plan",
            "speckit.tasks",
            "speckit.converge",
        ):
            self.assertIn(
                f'name: "{command}"',
                manifest,
            )

    def test_external_compatibility_claims_match_direct_evidence(self):
        extension = (
            EXTENSION_ROOT / "extension.yml"
        ).read_text(encoding="utf-8")
        preset = (
            PRESET_ROOT / "preset.yml"
        ).read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'speckit_version: "==1.0.7"',
            extension,
        )
        self.assertIn(
            'version: "==1.1.1"',
            extension,
        )
        self.assertIn(
            'speckit_version: "==1.0.7"',
            preset,
        )
        self.assertIn(
            'readonly SPECKIT_VERSION="1.0.7"',
            bootstrap,
        )
        self.assertIn(
            'readonly SPECDD_CLI_VERSION="1.1.1"',
            bootstrap,
        )
        self.assertIn(
            'readonly SPECDD_FRAMEWORK_VERSION="1.5"',
            bootstrap,
        )
        self.assertIn(
            "node --version",
            bootstrap,
        )
        self.assertIn(
            "uv run --no-project python --version",
            bootstrap,
        )

    def test_extension_declares_blocking_lifecycle_hooks(self):
        manifest = (
            EXTENSION_ROOT / "extension.yml"
        ).read_text(encoding="utf-8")

        for command in (
            "speckit.specdd.context",
            "speckit.specdd.validate",
            "speckit.specdd.authorize",
            "speckit.specdd.verify",
        ):
            self.assertIn(
                command,
                manifest,
            )

        for event in (
            "after_plan",
            "after_tasks",
            "before_implement",
            "after_implement",
        ):
            self.assertIn(
                f"{event}:",
                manifest,
            )

        self.assertEqual(
            4,
            manifest.count("optional: false"),
        )

        authorize = (
            EXTENSION_ROOT
            / "commands"
            / "authorize.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '--stage "implementation"',
            authorize,
        )
        self.assertIn(
            "`summary.blocking`",
            authorize,
        )

    def test_bootstrap_selects_registrar_backed_codex_integration(self):
        content = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'readonly ACTIVE_INTEGRATION="codex"',
            content,
        )
        self.assertIn(
            'readonly ACTIVE_COMMANDS_DIR=".agents/skills"',
            content,
        )
        self.assertIn(
            'specify integration switch "$ACTIVE_INTEGRATION" --script ps',
            content,
        )
        self.assertIn(
            "specify extension add integration/specdd --dev --force",
            content,
        )
        self.assertIn(
            "specify preset add --dev integration/specdd-preset --priority 10",
            content,
        )
        self.assertNotIn(
            "--integration generic",
            content,
        )

    def test_plan_fragment_projects_context_without_copying_constraints(self):
        content = (
            PRESET_ROOT / "commands" / "plan.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "## SpecDD Planning Augmentation",
            content,
        )
        self.assertIn(
            "speckit.specdd.context",
            content,
        )
        self.assertIn(
            "## SpecDD Impact",
            content,
        )
        self.assertIn(
            "Do not copy `Must`, `Must not`, `Owns`, or `Can modify`",
            content,
        )

    def test_task_fragment_preserves_story_grouping_and_authority_locality(self):
        content = (
            PRESET_ROOT / "commands" / "tasks.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(
            content.split()
        )

        self.assertIn(
            "Preserve Spec Kit user-story grouping",
            content,
        )
        self.assertIn(
            "one primary SpecDD authority",
            normalized,
        )
        self.assertIn(
            "`SPEC_EVOLUTION_REQUIRED:`",
            content,
        )
        self.assertIn(
            "`AUTHORITY_EVOLUTION_REQUIRED:`",
            content,
        )
        self.assertIn(
            "never combine an evolution task's `.sdd` targets",
            content,
        )
        self.assertIn(
            "separate follow-up task that refreshes `speckit.specdd.context`",
            content,
        )
        self.assertIn(
            "speckit.specdd.validate",
            content,
        )

    def test_converge_fragment_adds_specdd_diagnostics(self):
        content = (
            PRESET_ROOT / "commands" / "converge.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "speckit.specdd.verify",
            content,
        )
        for code in (
            "SPECDD_VIOLATION",
            "SPECDD_DRIFT",
            "MISSING_SPEC_EVOLUTION",
            "AUTHORITY_VIOLATION",
        ):
            self.assertIn(
                code,
                content,
            )
