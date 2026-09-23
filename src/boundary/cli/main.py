"""Top-level Boundary command-line entry point."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys
from typing import TextIO

from boundary.contracts import ContractGraphError, ContractParseError
from boundary.repository import RepositoryPathError

from .contracts import run_contracts_check
from .inspection import run_inspect


def build_parser() -> argparse.ArgumentParser:
    """Build the provider-neutral product command parser."""

    parser = argparse.ArgumentParser(
        prog="boundary",
        description="Persistent project contracts and operation authorization.",
    )
    commands = parser.add_subparsers(dest="command")

    contracts_parser = commands.add_parser(
        "contracts",
        help="Validate native project contracts.",
    )
    contract_commands = contracts_parser.add_subparsers(
        dest="contracts_command",
        required=True,
    )
    contract_commands.add_parser(
        "check",
        help="Validate canonical native contracts.",
    )

    inspect_parser = commands.add_parser(
        "inspect",
        help="Resolve effective contract context for repository targets.",
    )
    inspect_parser.add_argument(
        "targets",
        nargs="+",
        help="Repository-relative target path.",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    repository_root: str | Path | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the Boundary CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    output = stdout if stdout is not None else sys.stdout
    errors = stderr if stderr is not None else sys.stderr
    root = (
        Path.cwd()
        if repository_root is None
        else Path(repository_root)
    )

    try:
        if args.command == "contracts":
            return run_contracts_check(root, output)
        if args.command == "inspect":
            return run_inspect(root, args.targets, output)
    except (
        ContractParseError,
        ContractGraphError,
        RepositoryPathError,
        OSError,
    ) as exc:
        print(f"boundary: error: {exc}", file=errors)
        return 2

    parser.print_help(file=output)
    return 0
