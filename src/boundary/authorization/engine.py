"""Fresh canonical authorization for native Boundary operations."""

from pathlib import Path

from boundary.context import resolve_target_context
from boundary.contracts import ContractOwnershipError, load_contract_graph

from .identities import contract_graph_identity, effective_context_identity
from .model import (
    AuthorizationError,
    AuthorizedTarget,
    ChangeWriteSet,
    ContractEvolutionAuthorization,
    ContractEvolutionWriteSet,
    ImplementationAuthorization,
)


def authorize_implementation(
    repository_root: str | Path,
    change: ChangeWriteSet,
) -> ImplementationAuthorization:
    """Authorize exact implementation writes against a freshly loaded graph."""

    if not change.writes:
        raise AuthorizationError(
            "implementation authorization requires at least one "
            "declared write target"
        )

    graph = load_contract_graph(repository_root)
    targets: list[AuthorizedTarget] = []
    for path in change.writes:
        if is_native_contract_path(path):
            raise AuthorizationError(
                "implementation operations may not modify native contracts: "
                f"{path}"
            )
        try:
            context = resolve_target_context(graph, path)
        except ContractOwnershipError as exc:
            raise AuthorizationError(
                f"implementation write has ambiguous ownership: {path}"
            ) from exc
        if context.owner_id is None:
            raise AuthorizationError(
                f"implementation write has no primary owner: {path}"
            )
        targets.append(
            AuthorizedTarget(
                path=path,
                owner_id=context.owner_id,
                effective_context_identity=effective_context_identity(
                    graph,
                    context,
                ),
            )
        )

    return ImplementationAuthorization(
        change_id=change.change_id,
        tasks=change.tasks,
        targets=tuple(targets),
        contract_graph_identity=contract_graph_identity(graph),
    )


def authorize_contract_evolution(
    repository_root: str | Path,
    change: ContractEvolutionWriteSet,
) -> ContractEvolutionAuthorization:
    """Authorize exact native-contract writes separately from implementation."""

    if not change.writes:
        raise AuthorizationError(
            "contract-evolution authorization requires at least one target"
        )
    for path in change.writes:
        if not is_native_contract_path(path):
            raise AuthorizationError(
                "contract-evolution operations may modify only native "
                f"contracts: {path}"
            )

    graph = load_contract_graph(repository_root)
    return ContractEvolutionAuthorization(
        change_id=change.change_id,
        targets=change.writes,
        contract_graph_identity=contract_graph_identity(graph),
    )


def is_native_contract_path(path: str) -> bool:
    """Return whether a canonical path names a native Boundary contract."""

    return (
        path.startswith("contracts/")
        and path.endswith(".contract.md")
    )
