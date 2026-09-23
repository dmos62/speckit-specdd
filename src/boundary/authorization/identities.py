"""Deterministic identities for canonical authorization context."""

from hashlib import sha256
import json

from boundary.context import TargetContext
from boundary.contracts import ContractGraph


def contract_graph_identity(graph: ContractGraph) -> str:
    """Return a stable identity for the complete canonical contract graph."""

    contracts = sorted(
        graph.contracts,
        key=lambda contract: (
            contract.contract_id,
            contract.source_path,
        ),
    )
    payload = {
        "schema": "boundary.contract-graph-identity/v1",
        "contracts": [
            {
                "id": contract.contract_id,
                "source": contract.source_path,
                "content": contract.content_identity,
            }
            for contract in contracts
        ],
    }
    return _sha256_identity(payload)


def effective_context_identity(
    graph: ContractGraph,
    context: TargetContext,
) -> str:
    """Identify canonical contracts contributing to one effective context."""

    applicable = set(context.applicable_contract_ids)
    dependency_edges = tuple(
        sorted(
            (source_id, dependency_id)
            for source_id, dependency_id in graph.dependency_edges
            if source_id in applicable
        )
    )
    contributing = applicable | {
        dependency_id
        for _, dependency_id in dependency_edges
    }

    by_id = dict(graph.contracts_by_id)
    if not by_id:
        by_id = {
            contract.contract_id: contract
            for contract in graph.contracts
        }

    payload = {
        "schema": "boundary.effective-context-identity/v1",
        "target": context.target_path,
        "owner": context.owner_id,
        "contracts": [
            {
                "id": contract_id,
                "source": by_id[contract_id].source_path,
                "content": by_id[contract_id].content_identity,
            }
            for contract_id in sorted(contributing)
        ],
        "dependencyEdges": [
            [source_id, dependency_id]
            for source_id, dependency_id in dependency_edges
        ],
    }
    return _sha256_identity(payload)


def _sha256_identity(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"
