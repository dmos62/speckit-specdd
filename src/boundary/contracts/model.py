"""Provider-neutral contract data structures."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContractSections:
    """Recognized human-readable sections from one canonical contract."""

    purpose: str | None = None
    invariants: tuple[str, ...] = ()
    prohibitions: tuple[str, ...] = ()
    interfaces: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Contract:
    """One parsed canonical persistent contract."""

    contract_id: str
    source_path: str
    owns: tuple[str, ...]
    applies_to: tuple[str, ...]
    depends_on: tuple[str, ...]
    sections: ContractSections
    content_identity: str


@dataclass(frozen=True, slots=True)
class ScopeClaim:
    """A normalized scope associated with one contract."""

    scope: str
    contract_id: str


@dataclass(frozen=True, slots=True)
class ContractGraph:
    """Deterministic in-memory contract graph representation."""

    contracts: tuple[Contract, ...] = ()
    ownership_scopes: tuple[ScopeClaim, ...] = ()
    applicability_scopes: tuple[ScopeClaim, ...] = ()
    dependency_edges: tuple[tuple[str, str], ...] = ()
