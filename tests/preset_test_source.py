import unittest

from preset_test_support import (
    BOOTSTRAP_PATH,
    EXTENSION_ROOT,
    INSTALLER_PATH,
    PRESET_ROOT,
    SPECDD_FRAMEWORK_VERSION,
    SPECDD_PROVIDER_VERSION,
    SPECDD_UPSTREAM_CLI_VERSION,
    SPECKIT_VERSION,
)


class PresetSourceTests(unittest.TestCase):
    def test_manifests_preserve_pinned_composition_contract(self):
        extension = (
            EXTENSION_ROOT
            / "extension.yml"
        ).read_text(encoding="utf-8")
        preset = (
            PRESET_ROOT
            / "preset.yml"
        ).read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            f'speckit_version: "=={SPECKIT_VERSION}"',
            extension,
        )
        self.assertIn(
            f'version: "=={SPECDD_PROVIDER_VERSION}"',
            extension,
        )
        self.assertIn(
            f'speckit_version: "=={SPECKIT_VERSION}"',
            preset,
        )
        self.assertIn(
            'version: "==0.1.0"',
            preset,
        )
        self.assertEqual(
            3,
            preset.count('strategy: "append"'),
        )
        for command in (
            "speckit.plan",
            "speckit.tasks",
            "speckit.converge",
        ):
            self.assertIn(
                f'name: "{command}"',
                preset,
            )

        for declaration in (
            f'readonly SPECKIT_VERSION="{SPECKIT_VERSION}"',
            'readonly SPECKIT_TAG="v${SPECKIT_VERSION}"',
            (
                "readonly SPECDD_UPSTREAM_CLI_VERSION="
                f'"{SPECDD_UPSTREAM_CLI_VERSION}"'
            ),
            (
                "readonly SPECDD_COMPAT_CLI_VERSION="
                f'"{SPECDD_PROVIDER_VERSION}"'
            ),
            (
                "readonly SPECDD_FRAMEWORK_VERSION="
                f'"{SPECDD_FRAMEWORK_VERSION}"'
            ),
        ):
            self.assertIn(
                declaration,
                bootstrap,
            )

    def test_extension_declares_complete_lifecycle(self):
        manifest = (
            EXTENSION_ROOT
            / "extension.yml"
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

    def test_bootstrap_uses_shared_codex_installer(self):
        content = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        for marker in (
            'readonly ACTIVE_INTEGRATION="codex"',
            'readonly ACTIVE_COMMANDS_DIR=".agents/skills"',
            'specify integration switch "$ACTIVE_INTEGRATION" --script ps',
            "bash scripts/install.sh --source .",
        ):
            self.assertIn(
                marker,
                content,
            )

        for obsolete in (
            "specify extension add integration/specdd --dev --force",
            "specify preset add --dev integration/specdd-preset --priority 10",
            "specify workflow overlay add integration/specdd/workflow-overlay.yml",
            "--integration generic",
        ):
            self.assertNotIn(
                obsolete,
                content,
            )

    def test_installer_uses_native_components_and_immutable_remote_sources(self):
        content = INSTALLER_PATH.read_text(
            encoding="utf-8"
        )

        for marker in (
            'readonly SPECKIT_VERSION="1.0.10"',
            'readonly ACTIVE_INTEGRATION="codex"',
            "archive/refs/tags/",
            "releases/download/",
            "specify extension add",
            "specify preset add",
            "specify workflow overlay add",
            "specify workflow overlay remove",
            "specify integration switch",
        ):
            self.assertIn(
                marker,
                content,
            )

        for forbidden in (
            "npm install",
            "pip install",
            "specify bundle install",
        ):
            self.assertNotIn(
                forbidden,
                content,
            )

    def test_augmentations_cover_authority_aware_lifecycle(self):
        plan = (
            PRESET_ROOT
            / "commands"
            / "plan.md"
        ).read_text(encoding="utf-8")
        tasks = (
            PRESET_ROOT
            / "commands"
            / "tasks.md"
        ).read_text(encoding="utf-8")
        converge = (
            PRESET_ROOT
            / "commands"
            / "converge.md"
        ).read_text(encoding="utf-8")

        for marker in (
            "speckit.specdd.context",
            "## SpecDD Impact",
            "Do not copy `Must`, `Must not`, `Owns`, or `Can modify`",
        ):
            self.assertIn(
                marker,
                plan,
            )

        for marker in (
            "Preserve Spec Kit user-story grouping",
            "`SPEC_EVOLUTION_REQUIRED:`",
            "`AUTHORITY_EVOLUTION_REQUIRED:`",
            "speckit.specdd.authorize",
            "speckit.specdd.validate",
        ):
            self.assertIn(
                marker,
                tasks,
            )

        self.assertIn(
            "speckit.specdd.verify",
            converge,
        )
        for code in (
            "SPECDD_VIOLATION",
            "SPECDD_DRIFT",
            "MISSING_SPEC_EVOLUTION",
            "AUTHORITY_VIOLATION",
            "UNPLANNED_SPEC_EVOLUTION",
        ):
            self.assertIn(
                code,
                converge,
            )
