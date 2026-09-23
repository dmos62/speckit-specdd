"""Versioned atomic operation-record model."""

from dataclasses import dataclass, replace
import re
from uuid import uuid4

from boundary.repository import normalize_repo_path

from .model import (
    ContractEvolutionAuthorization,
    ImplementationAuthorization,
    TaskWriteSet,
)

_OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class DirtyPathState:
    """Exact identity of one dirty Git path."""

    path: str
    state: str

    def __post_init__(self) -> None:
        _validate_path(self.path)
        _validate_nonempty(self.state, "path state")


@dataclass(frozen=True, slots=True)
class GitBaseline:
    """Git state captured immediately before operation evidence is stored."""

    head: str | None
    dirty_path_states: tuple[DirtyPathState, ...] = ()

    def __post_init__(self) -> None:
        if self.head is not None:
            _validate_nonempty(self.head, "Git HEAD")
        _validate_unique_paths(
            self.dirty_path_states,
            "Git baseline dirty path",
        )


@dataclass(frozen=True, slots=True)
class CarriedForwardState:
    """Verified predecessor output adopted by one successor epoch."""

    path: str
    state: str
    operation_id: str

    def __post_init__(self) -> None:
        _validate_path(self.path)
        _validate_nonempty(self.state, "carried-forward state")
        _validate_operation_id(self.operation_id)


@dataclass(frozen=True, slots=True)
class OperationTargetEvidence:
    """Historical authorization evidence for one exact operation target."""

    path: str
    owner: str | None = None
    effective_context_identity: str | None = None

    def __post_init__(self) -> None:
        _validate_path(self.path)
        if self.owner is not None:
            _validate_nonempty(self.owner, "target owner")
        if self.effective_context_identity is not None:
            _validate_nonempty(
                self.effective_context_identity,
                "effective context identity",
            )


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
    carried_forward: tuple[CarriedForwardState, ...] = ()
    verification_final_states: tuple[DirtyPathState, ...] = ()
    status: str = "authorized"

    def __post_init__(self) -> None:
        _validate_operation_id(self.operation_id)
        _validate_nonempty(self.change_id, "change id")
        _validate_nonempty(
            self.contract_graph_identity,
            "contract graph identity",
        )
        if self.kind not in {"implementation", "contract-evolution"}:
            raise ValueError(f"unsupported operation kind: {self.kind!r}")
        if self.status not in {"authorized", "verified"}:
            raise ValueError(f"unsupported operation status: {self.status!r}")
        if self.kind == "contract-evolution" and self.tasks:
            raise ValueError(
                "contract-evolution operation must not contain tasks"
            )
        if self.status == "authorized" and self.verification_final_states:
            raise ValueError(
                "authorized operation cannot contain final verification states"
            )

        _validate_unique_paths(
            self.authorized_targets,
            "authorized target",
        )
        _validate_unique_paths(
            self.carried_forward,
            "carried-forward path",
        )
        _validate_unique_paths(
            self.verification_final_states,
            "verification final path",
        )

        target_paths = {
            target.path
            for target in self.authorized_targets
        }
        for item in self.carried_forward:
            if item.path not in target_paths:
                raise ValueError(
                    "carried-forward path is not an authorized target: "
                    f"{item.path}"
                )
        for item in self.verification_final_states:
            if item.path not in target_paths:
                raise ValueError(
                    "verification final path is not an authorized target: "
                    f"{item.path}"
                )

    def mark_verified(
        self,
        final_states: tuple[DirtyPathState, ...],
    ) -> "OperationRecord":
        """Return the closed verified form of this operation epoch."""

        return replace(
            self,
            status="verified",
            verification_final_states=tuple(final_states),
        )

    def to_document(self) -> dict[str, object]:
        """Project the record into its stable version-1 JSON document."""

        document: dict[str, object] = {
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
                "dirtyPathStates": _state_documents(
                    self.git_baseline.dirty_path_states
                ),
            },
            "carriedForward": [
                {
                    "path": item.path,
                    "state": item.state,
                    "operationId": item.operation_id,
                }
                for item in self.carried_forward
            ],
            "status": self.status,
        }
        if self.status == "verified":
            document["verification"] = {
                "finalPathStates": _state_documents(
                    self.verification_final_states
                ),
            }
        return document


def new_operation_id() -> str:
    """Create one filesystem-safe opaque operation identifier."""

    return uuid4().hex


def implementation_record(
    authorization: ImplementationAuthorization,
    baseline: GitBaseline,
    *,
    operation_id: str | None = None,
    carried_forward: tuple[CarriedForwardState, ...] = (),
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
        carried_forward=carried_forward,
    )


def contract_evolution_record(
    authorization: ContractEvolutionAuthorization,
    baseline: GitBaseline,
    *,
    operation_id: str | None = None,
    carried_forward: tuple[CarriedForwardState, ...] = (),
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
        carried_forward=carried_forward,
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


def _state_documents(
    states: tuple[DirtyPathState, ...],
) -> list[dict[str, str]]:
    return [
        {"path": item.path, "state": item.state}
        for item in states
    ]


def _validate_path(path: str) -> None:
    normalized = normalize_repo_path(path)
    if normalized != path:
        raise ValueError(
            f"operation path must be canonical: {path!r}"
        )


def _validate_nonempty(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _validate_operation_id(value: str) -> None:
    if not isinstance(value, str) or not _OPERATION_ID_RE.fullmatch(value):
        raise ValueError("operation id contains unsupported characters")


def _validate_unique_paths(
    values: tuple[object, ...],
    label: str,
) -> None:
    paths = [getattr(item, "path") for item in values]
    if len(paths) != len(set(paths)):
        raise ValueError(f"{label}s must be unique")
