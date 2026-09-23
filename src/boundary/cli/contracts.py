"""CLI operations for canonical native contracts."""

from pathlib import Path
from typing import TextIO

from boundary.contracts import load_contract_graph


def run_contracts_check(
    repository_root: Path,
    output: TextIO,
) -> int:
    """Validate canonical contracts and report a compact result."""

    graph = load_contract_graph(repository_root)
    count = len(graph.contracts)
    noun = "contract" if count == 1 else "contracts"
    print(
        f"contracts: ok ({count} {noun})",
        file=output,
    )
    return 0
