"""Deterministic effective-context resolution for repository targets."""

from boundary.contracts.errors import ContractOwnershipError
from boundary.contracts.model import Contract, ContractGraph, ScopeClaim
from boundary.contracts.scopes import scope_matches, scope_strictly_contains
from boundary.repository import normalize_repo_path

from .model import ProvenancedText, TargetContext


def resolve_target_context(
    graph: ContractGraph,
    target_path: str,
) -> TargetContext:
    """Resolve ownership and additive contract context for one target path."""

    target = normalize_repo_path(target_path)
    by_id = dict(graph.contracts_by_id)
    if not by_id:
        by_id = {
            contract.contract_id: contract
            for contract in graph.contracts
        }

    ownership_matches = tuple(
        claim
        for claim in graph.ownership_scopes
        if scope_matches(claim.scope, target)
    )
    owner_id = _primary_owner(ownership_matches)

    applicable_ids = tuple(
        sorted(
            {
                claim.contract_id
                for claim in graph.applicability_scopes
                if scope_matches(claim.scope, target)
            }
        )
    )
    applicable = tuple(
        by_id[contract_id]
        for contract_id in applicable_ids
    )
    dependencies = _direct_dependencies(graph, applicable_ids)

    return TargetContext(
        target_path=target,
        owner_id=owner_id,
        applicable_contract_ids=applicable_ids,
        purposes=_project_purposes(applicable),
        invariants=_project_items(applicable, "Invariants"),
        prohibitions=_project_items(applicable, "Prohibitions"),
        dependency_interfaces=_project_items(
            tuple(
                by_id[contract_id]
                for contract_id in dependencies
            ),
            "Interfaces",
        ),
        interfaces=_project_items(applicable, "Interfaces"),
    )


def _primary_owner(matches: tuple[ScopeClaim, ...]) -> str | None:
    if not matches:
        return None

    most_specific = [
        claim
        for claim in matches
        if not any(
            claim != other
            and scope_strictly_contains(
                claim.scope,
                other.scope,
            )
            for other in matches
        )
    ]
    owner_ids = {
        claim.contract_id
        for claim in most_specific
    }
    if len(owner_ids) == 1:
        return next(iter(owner_ids))

    claims = ", ".join(
        f"{claim.contract_id}:{claim.scope}"
        for claim in sorted(
            most_specific,
            key=lambda item: (item.scope, item.contract_id),
        )
    )
    raise ContractOwnershipError(
        f"ambiguous ownership for target: {claims}"
    )


def _direct_dependencies(
    graph: ContractGraph,
    applicable_ids: tuple[str, ...],
) -> tuple[str, ...]:
    sources = set(applicable_ids)
    return tuple(
        sorted(
            {
                dependency_id
                for source_id, dependency_id in graph.dependency_edges
                if source_id in sources
            }
        )
    )


def _project_purposes(
    contracts: tuple[Contract, ...],
) -> tuple[ProvenancedText, ...]:
    return tuple(
        _provenanced(
            contract,
            "Purpose",
            contract.sections.purpose,
        )
        for contract in contracts
        if contract.sections.purpose is not None
    )


def _project_items(
    contracts: tuple[Contract, ...],
    section: str,
) -> tuple[ProvenancedText, ...]:
    items: list[ProvenancedText] = []
    attribute = section.lower()
    for contract in contracts:
        for text in getattr(contract.sections, attribute):
            items.append(
                _provenanced(
                    contract,
                    section,
                    text,
                )
            )
    return tuple(items)


def _provenanced(
    contract: Contract,
    section: str,
    text: str,
) -> ProvenancedText:
    return ProvenancedText(
        text=text,
        contract_id=contract.contract_id,
        source_path=contract.source_path,
        section=section,
        content_identity=contract.content_identity,
    )
