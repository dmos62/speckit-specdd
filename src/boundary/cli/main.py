"""Top-level Boundary command-line entry point."""

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the provider-neutral product command parser."""

    return argparse.ArgumentParser(
        prog="boundary",
        description="Persistent project contracts and operation authorization.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Boundary CLI."""

    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
