"""Verification-epoch closure and final-state evidence capture."""

from pathlib import Path

from boundary.authorization.git import (
    capture_dirty_path_states,
    capture_git_head,
)
from boundary.authorization.model import AuthorizationError
from boundary.authorization.record import OperationRecord
from boundary.authorization.storage import (
    read_current_operation,
    write_current_operation,
)

from .errors import VerificationError


def finalize_operation_verification(
    repository_root: str | Path,
    *,
    operation_id: str | None = None,
) -> OperationRecord:
    """Close a successfully checked operation and record carry-forward state.

    Native actual-write checks are layered before this finalization step.
    This function protects the authorization baseline and records the exact
    dirty states that a later epoch may carry forward.
    """

    try:
        current = read_current_operation(repository_root)
    except AuthorizationError as exc:
        raise VerificationError(str(exc)) from exc

    if current is None:
        raise VerificationError(
            "no active Boundary operation is available for verification"
        )
    if operation_id is not None and current.operation_id != operation_id:
        raise VerificationError(
            "active operation changed before verification could be finalized"
        )
    if current.status == "verified":
        return current

    try:
        head = capture_git_head(repository_root)
    except AuthorizationError as exc:
        raise VerificationError(str(exc)) from exc
    if head != current.git_baseline.head:
        raise VerificationError(
            "GIT_BASELINE_CHANGED: Git HEAD changed after authorization; "
            "the active operation cannot be verified against its baseline"
        )

    try:
        dirty_states = capture_dirty_path_states(repository_root)
    except AuthorizationError as exc:
        raise VerificationError(str(exc)) from exc

    target_paths = {
        target.path
        for target in current.authorized_targets
    }
    final_states = tuple(
        state
        for state in dirty_states
        if state.path in target_paths
    )
    verified = current.mark_verified(final_states)

    try:
        write_current_operation(repository_root, verified)
    except AuthorizationError as exc:
        raise VerificationError(str(exc)) from exc
    return verified
