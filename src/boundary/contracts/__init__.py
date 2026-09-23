"""Native persistent-contract parsing and graph construction boundary."""

from .discovery import discover_contract_paths, load_contracts
from .errors import ContractParseError, ContractScopeError
from .model import Contract, ContractGraph, ContractSections, ScopeClaim
from .parser import parse_contract
from .scopes import normalize_contract_scope

__all__ = [
    "Contract",
    "ContractGraph",
    "ContractParseError",
    "ContractScopeError",
    "ContractSections",
    "ScopeClaim",
    "discover_contract_paths",
    "load_contracts",
    "normalize_contract_scope",
    "parse_contract",
]
