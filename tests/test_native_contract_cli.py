from hashlib import sha256
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from boundary.cli import main


PAYMENTS = """---
schema: boundary.contract/v1
id: payments
owns:
  - src/payments/**
applies_to:
  - src/api/payment-methods/**
depends_on:
  - users
---

# Payments

## Purpose

Process payments.

## Invariants

- Never persist card data.

## Prohibitions

- Keep providers isolated.
"""

STRIPE = """---
schema: boundary.contract/v1
id: stripe
owns:
  - src/payments/providers/stripe/**
---

# Stripe

## Invariants

- Use Stripe adapters.
"""

USERS = """---
schema: boundary.contract/v1
id: users
owns:
  - src/users/**
---

# Users

## Interfaces

- Use UserIdentity.
"""


class NativeContractCliTests(unittest.TestCase):
    def test_contracts_check_reports_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, "contracts/payments.contract.md", PAYMENTS)
            self._write(root, "contracts/users.contract.md", USERS)

            code, output, errors = self._run(
                root,
                "contracts",
                "check",
            )

            self.assertEqual(0, code)
            self.assertEqual(
                "contracts: ok (2 contracts)\n",
                output,
            )
            self.assertEqual("", errors)

    def test_contracts_check_reports_source_for_parse_diagnostics(self):
        source = """---
schema: boundary.contract/v1
id: broken
owns:
  - **
---
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                "contracts/broken.contract.md",
                source,
            )

            code, output, errors = self._run(
                root,
                "contracts",
                "check",
            )

            self.assertEqual(2, code)
            self.assertEqual("", output)
            self.assertEqual(
                "boundary: error: contracts/broken.contract.md: "
                "repository-wide '**' scope is not supported\n",
                errors,
            )

    def test_contracts_check_reports_ambiguous_ownership_sources(self):
        alpha = PAYMENTS.replace(
            "id: payments",
            "id: alpha",
        ).replace(
            "src/payments/**",
            "src/shared/**",
        ).replace(
            "  - users\n",
            "",
        ).replace(
            "applies_to:\n  - src/api/payment-methods/**\n",
            "",
        )
        beta = alpha.replace(
            "id: alpha",
            "id: beta",
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                "contracts/a.contract.md",
                alpha,
            )
            self._write(
                root,
                "contracts/b.contract.md",
                beta,
            )

            code, output, errors = self._run(
                root,
                "contracts",
                "check",
            )

            self.assertEqual(2, code)
            self.assertEqual("", output)
            self.assertIn(
                "contracts/a.contract.md",
                errors,
            )
            self.assertIn(
                "contracts/b.contract.md",
                errors,
            )
            self.assertIn(
                "ambiguous ownership",
                errors,
            )

    def test_inspect_is_stable_multi_target_and_transient(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                "contracts/payments.contract.md",
                PAYMENTS,
            )
            self._write(
                root,
                "contracts/stripe.contract.md",
                STRIPE,
            )
            self._write(
                root,
                "contracts/users.contract.md",
                USERS,
            )
            before = self._files(root)

            arguments = (
                "inspect",
                "src/payments/providers/stripe/client.py",
                "src/api/payment-methods/card.py",
            )
            first = self._run(root, *arguments)
            second = self._run(root, *arguments)

            self.assertEqual(first, second)
            self.assertEqual(0, first[0])
            self.assertEqual("", first[2])
            self.assertEqual(before, self._files(root))
            self.assertFalse((root / "src").exists())
            self.assertEqual(
                self._expected_inspection(),
                first[1],
            )

    def _run(
        self,
        root: Path,
        *arguments: str,
    ) -> tuple[int, str, str]:
        output = StringIO()
        errors = StringIO()
        code = main(
            arguments,
            repository_root=root,
            stdout=output,
            stderr=errors,
        )
        return code, output.getvalue(), errors.getvalue()

    def _write(
        self,
        root: Path,
        path: str,
        source: str,
    ) -> None:
        target = root / path
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        target.write_text(
            source,
            encoding="utf-8",
        )

    def _files(self, root: Path) -> tuple[str, ...]:
        return tuple(
            sorted(
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            )
        )

    def _expected_inspection(self) -> str:
        payments = self._identity(PAYMENTS)
        stripe = self._identity(STRIPE)
        users = self._identity(USERS)
        return f"""target: src/payments/providers/stripe/client.py
owner: stripe
applicable: payments, stripe
sources:
  payments: contracts/payments.contract.md @ {payments}
  stripe: contracts/stripe.contract.md @ {stripe}
  users: contracts/users.contract.md @ {users}
purpose:
  - payments: Process payments.
invariants:
  - payments: Never persist card data.
  - stripe: Use Stripe adapters.
prohibitions:
  - payments: Keep providers isolated.
dependency-interfaces:
  - users: Use UserIdentity.

target: src/api/payment-methods/card.py
owner: -
applicable: payments
sources:
  payments: contracts/payments.contract.md @ {payments}
  users: contracts/users.contract.md @ {users}
purpose:
  - payments: Process payments.
invariants:
  - payments: Never persist card data.
prohibitions:
  - payments: Keep providers isolated.
dependency-interfaces:
  - users: Use UserIdentity.
"""

    def _identity(self, source: str) -> str:
        digest = sha256(
            source.encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"


if __name__ == "__main__":
    unittest.main()
