"""Versioned atomic operation-record model."""

from dataclasses import dataclass
import re
from uuid import uuid4

from .model import (
    ContractEvolutionAuthorization,
    ImplementationAuthorization,
    TaskWriteSet,
)

_OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class DirtyPathState:
    """Authorization-time identity of one dirty Git path."""

    path: str
    state: str


@dataclass(frozen=True, slots=True)
class GitBaseline:
    """Git state captured immediately before operation evidence is stored."""

    head: str | None
    dirty_path_states: tuple[DirtyPathState, ...] = ()


@dataclass(frozen=True, slots=True)
class OperationTargetEvidence:
    """Historical authorization evidence for one exact operation target."""

    path: str
    owner: str | None = None
    effective_context_identity: str | None = None


@dataclass(frozen=True, slots=True)
class OperationRecord:
    """One versioned historical document for one authorized operation."""

    operation_id: str
    change_id: str
    kind: str
    tasks: tuple[TaskWriteSet, ...]
    authorized_targets: tuple[OperationTargetEvidence, ...]
    contract_graph_identity: str
    git_baseline: GitBaseline
    status: str = "authorized"

    def __post_init__(self) -> None:
        if not _OPERATION_ID_RE.fullmatch(self.operation_id):
            raise ValueError("operation id contains unsupported characters")
        if self.kind not in {"implementation", "contract-evolution"}:
            raise ValueError(f"unsupported operation kind: {self.kind!r}")

    def to_document(self) -> dict[str, object]:
        """Project the record into its stable version-1 JSON document."""

        return {
            "schemaVersion": 1,
            "operationId": self.operation_id,
            "changeId": self.change_id,
            "kind": self.kind,
            "tasks": [
                {
                    "order": task.order,
                    "id": task.task_id,
                    "story": task.story,
                    "writes": list(task.writes),
                }
                for task in self.tasks
            ],
            "authorizedTargets": [
                _target_document(target)
                for target in self.authorized_targets
            ],
            "contractGraphIdentity": self.contract_graph_identity,
            "gitBaseline": {
                "head": self.git_baseline.head,
                "dirtyPathStates": [
                    {
                        "path": item.path,
                        "state": item.state,
                    }
                    for item in self.git_baseline.dirty_path_states
                ],
            },
            "carriedForward": [],
            "status": self.status,
        }


def new_operation_id() -> str:
    """Create one filesystem-safe opaque operation identifier."""

    return uuid4().hex


def implementation_record(
    authorization: ImplementationAuthorization,
    baseline: GitBaseline,
    *,
    operation_id: str | None = None,
) -> OperationRecord:
    """Build an operation record from fresh implementation authorization."""

    return OperationRecord(
        operation_id=operation_id or new_operation_id(),
        change_id=authorization.change_id,
        kind="implementation",
        tasks=authorization.tasks,
        authorized_targets=tuple(
            OperationTargetEvidence(
                path=target.path,
                owner=target.owner_id,
                effective_context_identity=(
                    target.effective_context_identity
                ),
            )
            for target in authorization.targets
        ),
        contract_graph_identity=authorization.contract_graph_identity,
        git_baseline=baseline,
    )


def contract_evolution_record(
    authorization: ContractEvolutionAuthorization,
    baseline: GitBaseline,
    *,
    operation_id: str | None = None,
) -> OperationRecord:
    """Build an isolated contract-evolution operation record."""

    return OperationRecord(
        operation_id=operation_id or new_operation_id(),
        change_id=authorization.change_id,
        kind="contract-evolution",
        tasks=(),
        authorized_targets=tuple(
            OperationTargetEvidence(path=path)
            for path in authorization.targets
        ),
        contract_graph_identity=authorization.contract_graph_identity,
        git_baseline=baseline,
    )


def _target_document(
    target: OperationTargetEvidence,
) -> dict[str, object]:
    value: dict[str, object] = {"path": target.path}
    if target.owner is not None:
        value["owner"] = target.owner
    if target.effective_context_identity is not None:
        value["effectiveContextIdentity"] = (
            target.effective_context_identity
        )
    return value
