from pathlib import Path
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from boundary.contracts import (
    ContractParseError,
    ContractScopeError,
    discover_contract_paths,
    load_contracts,
    normalize_contract_scope,
    parse_contract,
)


CONTRACT = """---
schema: boundary.contract/v1
id: payments
owns:
  - src/payments/**
applies_to:
  - src/api/payment-methods/**
depends_on: [users]
---

# Payments

## Purpose

Own payment processing and provider integration.

## Invariants

- Raw card data is never persisted.
- Provider details remain behind the provider interface.

## Prohibitions

- Payment code must not depend on user persistence internals.

## Interfaces

- Consumers use the public payment-provider interface.
"""


class NativeContractParsingTests(unittest.TestCase):
    def test_parses_v1_frontmatter_and_semantic_sections(self):
        contract = parse_contract(
            CONTRACT,
            "contracts/payments.contract.md",
        )

        self.assertEqual("payments", contract.contract_id)
        self.assertEqual(("src/payments/**",), contract.owns)
        self.assertEqual(
            ("src/api/payment-methods/**",),
            contract.applies_to,
        )
        self.assertEqual(("users",), contract.depends_on)
        self.assertEqual(
            "Own payment processing and provider integration.",
            contract.sections.purpose,
        )
        self.assertEqual(
            (
                "Raw card data is never persisted.",
                "Provider details remain behind the provider interface.",
            ),
            contract.sections.invariants,
        )
        self.assertEqual(
            (
                "Payment code must not depend on user persistence internals.",
            ),
            contract.sections.prohibitions,
        )
        self.assertEqual(
            (
                "Consumers use the public payment-provider interface.",
            ),
            contract.sections.interfaces,
        )
        self.assertRegex(
            contract.content_identity,
            r"^sha256:[0-9a-f]{64}$",
        )

    def test_content_identity_is_stable_across_platform_line_endings(self):
        lf = parse_contract(
            CONTRACT,
            "contracts/payments.contract.md",
        )
        crlf = parse_contract(
            CONTRACT.replace("\n", "\r\n"),
            "contracts/payments.contract.md",
        )
        self.assertEqual(lf.content_identity, crlf.content_identity)

    def test_requires_v1_schema_id_and_at_least_one_scope(self):
        invalid_sources = (
            CONTRACT.replace(
                "boundary.contract/v1",
                "boundary.contract/v2",
            ),
            CONTRACT.replace("id: payments\n", ""),
            "---\nschema: boundary.contract/v1\nid: empty\n---\n",
        )
        for source in invalid_sources:
            with self.subTest(source=source[:60]):
                with self.assertRaises(ContractParseError):
                    parse_contract(
                        source,
                        "contracts/test.contract.md",
                    )

    def test_rejects_unknown_or_duplicate_frontmatter_fields(self):
        unknown = CONTRACT.replace(
            "id: payments\n",
            "id: payments\nowner: team-a\n",
        )
        duplicate = CONTRACT.replace(
            "id: payments\n",
            "id: payments\nid: duplicate\n",
        )
        for source in (unknown, duplicate):
            with self.subTest(source=source[:80]):
                with self.assertRaises(ContractParseError):
                    parse_contract(
                        source,
                        "contracts/test.contract.md",
                    )

    def test_rejects_duplicate_recognized_sections(self):
        source = CONTRACT + "\n## Invariants\n\n- Another invariant.\n"
        with self.assertRaises(ContractParseError):
            parse_contract(
                source,
                "contracts/test.contract.md",
            )


class NativeContractScopeTests(unittest.TestCase):
    def test_accepts_only_exact_and_subtree_scopes(self):
        self.assertEqual(
            "src/auth/service.py",
            normalize_contract_scope("src/auth/service.py"),
        )
        self.assertEqual(
            "src/auth/**",
            normalize_contract_scope("src/auth/**"),
        )

    def test_rejects_catch_all_globs_and_noncanonical_paths(self):
        invalid = (
            "**",
            "src/*/service.py",
            "src/{auth,users}/**",
            "src/**/generated/*.py",
            "./src/auth/**",
            "src/../auth/**",
            "/src/auth/**",
        )
        for scope in invalid:
            with self.subTest(scope=scope):
                with self.assertRaises(ContractScopeError):
                    normalize_contract_scope(scope)


class NativeContractDiscoveryTests(unittest.TestCase):
    def test_discovers_only_contract_tree_in_deterministic_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "contracts" / "nested").mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "contracts" / "z.contract.md").write_text(
                CONTRACT.replace("id: payments", "id: zed"),
                encoding="utf-8",
            )
            (
                root
                / "contracts"
                / "nested"
                / "a.contract.md"
            ).write_text(
                CONTRACT.replace("id: payments", "id: alpha"),
                encoding="utf-8",
            )
            (root / "contracts" / "ignored.md").write_text(
                CONTRACT,
                encoding="utf-8",
            )
            (root / "docs" / "outside.contract.md").write_text(
                CONTRACT,
                encoding="utf-8",
            )

            self.assertEqual(
                (
                    "contracts/nested/a.contract.md",
                    "contracts/z.contract.md",
                ),
                discover_contract_paths(root),
            )
            self.assertEqual(
                ("alpha", "zed"),
                tuple(
                    contract.contract_id
                    for contract in load_contracts(root)
                ),
            )

    def test_missing_contract_directory_discovers_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                (),
                discover_contract_paths(directory),
            )
            self.assertEqual((), load_contracts(directory))


if __name__ == "__main__":
    unittest.main()
