"""Construction and validation of deterministic native contract graphs."""

from collections.abc import Iterable

from .errors import (
    ContractDependencyError,
    ContractGraphError,
    ContractOwnershipError,
)
from .model import Contract, ContractGraph, ScopeClaim
from .scopes import scope_strictly_contains, scopes_overlap


def build_contract_graph(contracts: Iterable[Contract]) -> ContractGraph:
    """Build deterministic indexes from parsed canonical contracts."""

    ordered = tuple(sorted(contracts, key=lambda contract: contract.contract_id))
    by_id: dict[str, Contract] = {}
    for contract in ordered:
        if contract.contract_id in by_id:
            raise ContractGraphError(
                f"duplicate contract id {contract.contract_id!r}"
            )
        by_id[contract.contract_id] = contract

    ownership = _scope_claims(ordered, include_applies_to=False)
    _validate_ownership(ownership)
    applicability = _scope_claims(ordered, include_applies_to=True)
    dependencies = _dependency_edges(ordered, by_id)
    return ContractGraph(
        contracts=ordered,
        ownership_scopes=ownership,
        applicability_scopes=applicability,
        dependency_edges=dependencies,
        contracts_by_id=tuple(
            (contract.contract_id, contract)
            for contract in ordered
        ),
    )


def _scope_claims(
    contracts: tuple[Contract, ...],
    *,
    include_applies_to: bool,
) -> tuple[ScopeClaim, ...]:
    claims: set[ScopeClaim] = set()
    for contract in contracts:
        scopes = contract.owns
        if include_applies_to:
            scopes = contract.owns + contract.applies_to
        for scope in scopes:
            claims.add(
                ScopeClaim(
                    scope=scope,
                    contract_id=contract.contract_id,
                )
            )
    return tuple(
        sorted(
            claims,
            key=lambda claim: (claim.scope, claim.contract_id),
        )
    )


def _validate_ownership(claims: tuple[ScopeClaim, ...]) -> None:
    for index, left in enumerate(claims):
        for right in claims[index + 1 :]:
            if left.contract_id == right.contract_id:
                continue
            if not scopes_overlap(left.scope, right.scope):
                continue
            if scope_strictly_contains(left.scope, right.scope):
                continue
            if scope_strictly_contains(right.scope, left.scope):
                continue
            raise ContractOwnershipError(
                "ambiguous ownership between "
                f"{left.contract_id!r} ({left.scope}) and "
                f"{right.contract_id!r} ({right.scope})"
            )


def _dependency_edges(
    contracts: tuple[Contract, ...],
    by_id: dict[str, Contract],
) -> tuple[tuple[str, str], ...]:
    edges: set[tuple[str, str]] = set()
    for contract in contracts:
        for dependency_id in contract.depends_on:
            if dependency_id == contract.contract_id:
                raise ContractDependencyError(
                    f"contract {contract.contract_id!r} cannot depend on itself"
                )
            if dependency_id not in by_id:
                raise ContractDependencyError(
                    f"contract {contract.contract_id!r} depends on unknown "
                    f"contract {dependency_id!r}"
                )
            edges.add((contract.contract_id, dependency_id))
    return tuple(sorted(edges))
