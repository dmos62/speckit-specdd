"""Native persistent-contract parsing and graph construction boundary."""

from .discovery import discover_contract_paths, load_contract_graph, load_contracts
from .errors import (
    ContractDependencyError,
    ContractGraphError,
    ContractOwnershipError,
    ContractParseError,
    ContractScopeError,
)
from .graph import build_contract_graph
from .model import Contract, ContractGraph, ContractSections, ScopeClaim
from .parser import parse_contract
from .scopes import (
    normalize_contract_scope,
    scope_matches,
    scope_strictly_contains,
    scopes_overlap,
)

__all__ = [
    "Contract",
    "ContractDependencyError",
    "ContractGraph",
    "ContractGraphError",
    "ContractOwnershipError",
    "ContractParseError",
    "ContractScopeError",
    "ContractSections",
    "ScopeClaim",
    "build_contract_graph",
    "discover_contract_paths",
    "load_contract_graph",
    "load_contracts",
    "normalize_contract_scope",
    "parse_contract",
    "scope_matches",
    "scope_strictly_contains",
    "scopes_overlap",
]
