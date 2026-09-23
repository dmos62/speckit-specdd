from pathlib import Path
import sys
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import boundary.authorization as authorization
import boundary.verification as verification
from boundary.cli import build_parser
from boundary.contracts import Contract, ContractGraph, ContractSections
from boundary.context import TargetContext
from boundary.repository import RepositoryPathError, normalize_repo_path


class BoundaryCoreLayoutTests(unittest.TestCase):
    def test_provider_neutral_component_boundaries_import(self):
        contract = Contract(
            contract_id="auth",
            source_path="contracts/auth.contract.md",
            owns=("src/auth/**",),
            applies_to=(),
            depends_on=(),
            sections=ContractSections(),
            content_identity="sha256:test",
        )
        graph = ContractGraph(contracts=(contract,))
        context = TargetContext(target_path="src/auth/service.py", owner_id="auth")

        self.assertEqual("auth", graph.contracts[0].contract_id)
        self.assertEqual("auth", context.owner_id)
        self.assertEqual("boundary.authorization", authorization.__name__)
        self.assertEqual("boundary.verification", verification.__name__)

    def test_repository_paths_are_normalized_without_filesystem_access(self):
        self.assertEqual(
            "src/auth/service.py",
            normalize_repo_path("./src/auth/./service.py"),
        )

    def test_repository_paths_reject_non_repository_forms(self):
        invalid = ("", ".", "/tmp/file.py", "../file.py", "src/../file.py", "src\\file.py")
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(RepositoryPathError):
                    normalize_repo_path(value)

    def test_cli_uses_product_identity(self):
        parser = build_parser()
        self.assertEqual("boundary", parser.prog)

    def test_core_source_does_not_name_integration_providers(self):
        forbidden = ("specdd", "speckit", "codex")
        for source_path in sorted((SOURCE_ROOT / "boundary").rglob("*.py")):
            source = source_path.read_text(encoding="utf-8").lower()
            for provider in forbidden:
                with self.subTest(path=source_path, provider=provider):
                    self.assertNotIn(provider, source)


if __name__ == "__main__":
    unittest.main()
