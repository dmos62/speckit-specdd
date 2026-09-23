"""End-to-end native authorization and historical evidence creation."""

from pathlib import Path

from .engine import authorize_contract_evolution, authorize_implementation
from .git import capture_git_baseline
from .model import (
    AuthorizationError,
    ChangeWriteSet,
    ContractEvolutionWriteSet,
)
from .record import (
    CarriedForwardState,
    GitBaseline,
    OperationRecord,
    contract_evolution_record,
    implementation_record,
)
from .storage import (
    archive_operation,
    read_current_operation,
    write_current_operation,
)


def authorize_implementation_operation(
    repository_root: str | Path,
    change: ChangeWriteSet,
    *,
    operation_id: str | None = None,
) -> OperationRecord:
    """Fresh-authorize implementation and atomically persist its evidence."""

    authorization = authorize_implementation(repository_root, change)
    baseline = capture_git_baseline(repository_root)
    predecessor, carried = _carry_forward(
        repository_root,
        baseline,
        change_id=change.change_id,
        kind="implementation",
        targets=authorization.writes,
    )
    record = implementation_record(
        authorization,
        baseline,
        operation_id=operation_id,
        carried_forward=carried,
    )
    _store_successor(
        repository_root,
        predecessor,
        record,
    )
    return record


def authorize_contract_evolution_operation(
    repository_root: str | Path,
    change: ContractEvolutionWriteSet,
    *,
    operation_id: str | None = None,
) -> OperationRecord:
    """Fresh-authorize contract evolution and persist isolated evidence."""

    authorization = authorize_contract_evolution(repository_root, change)
    baseline = capture_git_baseline(repository_root)
    predecessor, carried = _carry_forward(
        repository_root,
        baseline,
        change_id=change.change_id,
        kind="contract-evolution",
        targets=authorization.targets,
    )
    record = contract_evolution_record(
        authorization,
        baseline,
        operation_id=operation_id,
        carried_forward=carried,
    )
    _store_successor(
        repository_root,
        predecessor,
        record,
    )
    return record


def _carry_forward(
    repository_root: str | Path,
    baseline: GitBaseline,
    *,
    change_id: str,
    kind: str,
    targets: tuple[str, ...],
) -> tuple[
    OperationRecord | None,
    tuple[CarriedForwardState, ...],
]:
    predecessor = read_current_operation(repository_root)
    if predecessor is not None and predecessor.status != "verified":
        raise AuthorizationError(
            "OPERATION_NOT_VERIFIED: the active operation must be "
            "verified before another authorization epoch can replace it"
        )

    dirty = {
        item.path: item.state
        for item in baseline.dirty_path_states
    }
    dirty_targets = tuple(
        path
        for path in targets
        if path in dirty
    )
    if not dirty_targets:
        return predecessor, ()

    if predecessor is None:
        raise AuthorizationError(
            "DIRTY_TARGET_NOT_VERIFIED: intended target already contains "
            f"dirty state without predecessor provenance: {dirty_targets[0]}"
        )
    if (
        predecessor.change_id != change_id
        or predecessor.kind != kind
    ):
        raise AuthorizationError(
            "DIRTY_TARGET_NOT_VERIFIED: verified predecessor belongs to "
            "a different change or operation kind"
        )

    verified = {
        item.path: item.state
        for item in predecessor.verification_final_states
    }
    carried: list[CarriedForwardState] = []
    for path in dirty_targets:
        current_state = dirty[path]
        if verified.get(path) != current_state:
            raise AuthorizationError(
                "DIRTY_TARGET_NOT_VERIFIED: intended dirty target does not "
                f"match verified predecessor output: {path}"
            )
        carried.append(
            CarriedForwardState(
                path=path,
                state=current_state,
                operation_id=predecessor.operation_id,
            )
        )
    return predecessor, tuple(carried)


def _store_successor(
    repository_root: str | Path,
    predecessor: OperationRecord | None,
    record: OperationRecord,
) -> None:
    if record.carried_forward:
        if predecessor is None:
            raise AuthorizationError(
                "carry-forward requires a verified predecessor"
            )
        archive_operation(repository_root, predecessor)
    write_current_operation(repository_root, record)
