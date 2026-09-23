"""Deterministic discovery and loading of canonical Boundary contracts."""

from pathlib import Path

from .errors import ContractParseError
from .graph import build_contract_graph
from .model import Contract, ContractGraph
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
        contract_path = root / source_path
        try:
            source = contract_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContractParseError(
                f"{source_path}: contract source must be UTF-8"
            ) from exc
        except OSError as exc:
            detail = exc.strerror or exc.__class__.__name__
            raise ContractParseError(
                f"{source_path}: cannot read contract: {detail}"
            ) from exc

        try:
            contract = parse_contract(source, source_path)
        except ContractParseError as exc:
            error_type = type(exc)
            raise error_type(
                f"{source_path}: {exc}"
            ) from exc
        contracts.append(contract)

    return tuple(contracts)


def load_contract_graph(repository_root: str | Path) -> ContractGraph:
    """Load canonical contracts and build their deterministic in-memory graph."""

    return build_contract_graph(load_contracts(repository_root))
