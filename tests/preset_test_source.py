import unittest

from preset_test_support import (
    BOOTSTRAP_PATH,
    BOOTSTRAP_PROVIDER_PATH,
    EXTENSION_ROOT,
    INSTALLER_PATH,
    INSTALL_SOURCE_PATH,
    PRESET_ROOT,
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
        self.assertNotIn(
            'name: specdd',
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
            1,
            preset.count('strategy: "append"'),
        )
        self.assertIn(
            'name: "speckit.tasks"',
            preset,
        )
        self.assertNotIn(
            'name: "speckit.plan"',
            preset,
        )
        self.assertNotIn(
            'name: "speckit.converge"',
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
        ):
            self.assertIn(
                declaration,
                bootstrap,
            )

    def test_extension_exposes_only_boundary_adapter_transitions(self):
        manifest = (
            EXTENSION_ROOT
            / "extension.yml"
        ).read_text(encoding="utf-8")

        for command in (
            "speckit.boundary.authorize",
            "speckit.boundary.verify",
        ):
            self.assertIn(command, manifest)

        for obsolete in (
            "speckit.specdd.context",
            "speckit.specdd.validate",
            "speckit.specdd.authorize",
            "speckit.specdd.verify",
            "hooks:",
            "after_plan:",
            "after_tasks:",
            "before_implement:",
            "after_implement:",
        ):
            self.assertNotIn(obsolete, manifest)

    def test_bootstrap_uses_shared_codex_installer(self):
        content = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        for marker in (
            'readonly ACTIVE_INTEGRATION="codex"',
            'readonly ACTIVE_COMMANDS_DIR=".agents/skills"',
            'source "$BOOTSTRAP_SCRIPT_DIR/bootstrap-provider.sh"',
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

    def test_bootstrap_does_not_require_specdd_framework_bootstrap(self):
        content = BOOTSTRAP_PATH.read_text(
            encoding="utf-8"
        )

        for obsolete in (
            "SPECDD_FRAMEWORK_VERSION",
            "specdd_framework_version",
            "specdd init",
            ".specdd/bootstrap.md",
        ):
            self.assertNotIn(
                obsolete,
                content,
            )

    def test_installer_materializes_native_runtime_without_specdd_requirement(self):
        installer = INSTALLER_PATH.read_text(
            encoding="utf-8"
        )
        source_helper = INSTALL_SOURCE_PATH.read_text(
            encoding="utf-8"
        )
        content = installer + "\n" + source_helper

        for marker in (
            'readonly SPECKIT_VERSION="1.0.10"',
            'readonly ACTIVE_INTEGRATION="codex"',
            'readonly CODEX_SKILL_ADAPTER="adapters/codex/materialize.py"',
            'readonly BOUNDARY_RUNTIME_DIR=".specify/boundary-runtime"',
            'source "$INSTALL_SCRIPT_DIR/install-source.sh"',
            "archive/refs/tags/",
            "releases/download/",
            "specify extension add",
            "specify preset add",
            "specify workflow overlay add",
            "specify workflow overlay remove",
            "specify integration switch",
            "materialize_boundary_runtime",
            "materialize_boundary_skills",
            "src/boundary/__init__.py",
        ):
            self.assertIn(
                marker,
                content,
            )

        for forbidden in (
            "require_command specdd",
            "specdd resolve --help",
            "npm install",
            "pip install",
            "specify bundle install",
        ):
            self.assertNotIn(
                forbidden,
                installer,
            )

    def test_split_shell_sources_remain_small(self):
        for path in (
            BOOTSTRAP_PATH,
            BOOTSTRAP_PROVIDER_PATH,
            INSTALLER_PATH,
            INSTALL_SOURCE_PATH,
        ):
            with self.subTest(path=path.name):
                self.assertLessEqual(
                    len(path.read_text(encoding="utf-8").splitlines()),
                    250,
                )

    def test_task_augmentation_uses_on_demand_inspection_and_exact_writes(self):
        tasks = (
            PRESET_ROOT
            / "commands"
            / "tasks.md"
        ).read_text(encoding="utf-8")

        for marker in (
            "## Boundary Write Scope",
            "boundary inspect <target...>",
            "Writes:",
            "speckit.boundary.authorize",
            "Do not create or refresh a persisted Boundary context projection",
            "Do not add a separate validation lifecycle phase",
        ):
            self.assertIn(marker, tasks)

        for obsolete in (
            "speckit.specdd.context",
            "speckit.specdd.validate",
            "SPECDD_AUTHORITY:",
        ):
            self.assertNotIn(obsolete, tasks)
