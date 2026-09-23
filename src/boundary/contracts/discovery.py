"""Deterministic discovery and loading of canonical Boundary contracts."""

from pathlib import Path

from .model import Contract
from .parser import parse_contract


def discover_contract_paths(
    repository_root: str | Path,
) -> tuple[str, ...]:
    """Return canonical contract source paths in deterministic repository order."""

    root = Path(repository_root)
    contract_root = root / "contracts"
    if not contract_root.is_dir():
        return ()

    paths = (
        path.relative_to(root).as_posix()
        for path in contract_root.rglob("*.contract.md")
        if path.is_file()
    )
    return tuple(sorted(paths))


def load_contracts(repository_root: str | Path) -> tuple[Contract, ...]:
    """Discover and parse all canonical native contracts under a repository root."""

    root = Path(repository_root)
    contracts: list[Contract] = []
    for source_path in discover_contract_paths(root):
        source = (root / source_path).read_text(encoding="utf-8")
        contracts.append(parse_contract(source, source_path))
    return tuple(contracts)
