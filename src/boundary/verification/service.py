"""Git-derived native authorization verification and epoch closure."""

from pathlib import Path

from boundary.authorization.model import AuthorizationError
from boundary.authorization.record import OperationRecord
from boundary.authorization.storage import (
    read_current_operation,
    write_current_operation,
)

from .checks import (
    classify_actual_paths,
    diagnostic,
    verify_checked_writes,
)
from .errors import VerificationError
from .git import capture_git_delta
from .model import PathClassifier, VerificationDiagnostic, VerificationResult


def verify_operation_authorization(
    repository_root: str | Path,
    *,
    operation_id: str | None = None,
    classify_path: PathClassifier | None = None,
) -> VerificationResult:
    """Check actual Git writes against one historical operation record."""

    current = _load_current(repository_root)
    _require_operation(current, operation_id)
    if current.status == "verified":
        return VerificationResult(operation=current)

    try:
        delta = capture_git_delta(
            repository_root,
            current.git_baseline,
        )
    except AuthorizationError as exc:
        raise VerificationError(
            diagnostic("GIT_STATE_UNAVAILABLE", str(exc))
        ) from exc

    diagnostics: list[VerificationDiagnostic] = []
    if delta.head != current.git_baseline.head:
        diagnostics.append(
            diagnostic(
                "GIT_BASELINE_CHANGED",
                "Git HEAD changed after authorization; the active operation "
                "cannot be verified against its baseline",
            )
        )
        return VerificationResult(
            operation=current,
            dirty_path_states=delta.dirty_path_states,
            diagnostics=tuple(diagnostics),
        )

    checked, excluded = classify_actual_paths(
        current,
        delta.actual_paths,
        classify_path,
        diagnostics,
    )
    diagnostics.extend(
        verify_checked_writes(
            repository_root,
            current,
            checked,
        )
    )
    return VerificationResult(
        operation=current,
        actual_paths=delta.actual_paths,
        checked_writes=checked,
        excluded_paths=excluded,
        dirty_path_states=delta.dirty_path_states,
        diagnostics=tuple(diagnostics),
    )


def finalize_operation_verification(
    repository_root: str | Path,
    *,
    operation_id: str | None = None,
    classify_path: PathClassifier | None = None,
) -> OperationRecord:
    """Verify actual writes, close the epoch, and record final target states."""

    result = verify_operation_authorization(
        repository_root,
        operation_id=operation_id,
        classify_path=classify_path,
    )
    current = result.operation
    if current.status == "verified":
        return current
    if result.blocking:
        raise VerificationError(result.diagnostics)

    target_paths = {
        target.path
        for target in current.authorized_targets
    }
    final_states = tuple(
        state
        for state in result.dirty_path_states
        if state.path in target_paths
    )
    verified = current.mark_verified(final_states)
    try:
        write_current_operation(repository_root, verified)
    except AuthorizationError as exc:
        raise VerificationError(str(exc)) from exc
    return verified


def _load_current(
    repository_root: str | Path,
) -> OperationRecord:
    try:
        current = read_current_operation(repository_root)
    except AuthorizationError as exc:
        raise VerificationError(
            diagnostic("OPERATION_EVIDENCE_INVALID", str(exc))
        ) from exc
    if current is None:
        raise VerificationError(
            diagnostic(
                "NO_ACTIVE_OPERATION",
                "no active Boundary operation is available for verification",
            )
        )
    return current


def _require_operation(
    current: OperationRecord,
    operation_id: str | None,
) -> None:
    if operation_id is not None and current.operation_id != operation_id:
        raise VerificationError(
            diagnostic(
                "OPERATION_CHANGED",
                "active operation changed before verification could be "
                "finalized",
            )
        )
