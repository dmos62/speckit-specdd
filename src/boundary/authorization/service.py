"""End-to-end native authorization and historical evidence creation."""

from pathlib import Path

from .engine import authorize_contract_evolution, authorize_implementation
from .git import capture_git_baseline
from .model import ChangeWriteSet, ContractEvolutionWriteSet
from .record import (
    OperationRecord,
    contract_evolution_record,
    implementation_record,
)
from .storage import write_current_operation


def authorize_implementation_operation(
    repository_root: str | Path,
    change: ChangeWriteSet,
    *,
    operation_id: str | None = None,
) -> OperationRecord:
    """Fresh-authorize implementation and atomically persist its evidence."""

    authorization = authorize_implementation(repository_root, change)
    baseline = capture_git_baseline(repository_root)
    record = implementation_record(
        authorization,
        baseline,
        operation_id=operation_id,
    )
    write_current_operation(repository_root, record)
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
    record = contract_evolution_record(
        authorization,
        baseline,
        operation_id=operation_id,
    )
    write_current_operation(repository_root, record)
    return record
