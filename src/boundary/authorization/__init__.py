"""Provider-neutral native operation authorization boundary."""

from .engine import (
    authorize_contract_evolution,
    authorize_implementation,
    is_native_contract_path,
)
from .git import capture_git_baseline
from .identities import contract_graph_identity, effective_context_identity
from .model import (
    AuthorizationError,
    AuthorizedTarget,
    ChangeWriteSet,
    ContractEvolutionAuthorization,
    ContractEvolutionWriteSet,
    ImplementationAuthorization,
    TaskWriteSet,
    WriteSetError,
)
from .record import (
    DirtyPathState,
    GitBaseline,
    OperationRecord,
    OperationTargetEvidence,
)
from .service import (
    authorize_contract_evolution_operation,
    authorize_implementation_operation,
)
from .storage import current_operation_path, write_current_operation

__all__ = [
    "AuthorizationError",
    "AuthorizedTarget",
    "ChangeWriteSet",
    "ContractEvolutionAuthorization",
    "ContractEvolutionWriteSet",
    "DirtyPathState",
    "GitBaseline",
    "ImplementationAuthorization",
    "OperationRecord",
    "OperationTargetEvidence",
    "TaskWriteSet",
    "WriteSetError",
    "authorize_contract_evolution",
    "authorize_contract_evolution_operation",
    "authorize_implementation",
    "authorize_implementation_operation",
    "capture_git_baseline",
    "contract_graph_identity",
    "current_operation_path",
    "effective_context_identity",
    "is_native_contract_path",
    "write_current_operation",
]
