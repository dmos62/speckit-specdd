"""Git-derived actual-write calculation for native verification."""

from dataclasses import dataclass
from pathlib import Path

from boundary.authorization.git import (
    capture_dirty_path_states,
    capture_git_head,
    path_state,
)
from boundary.authorization.model import AuthorizationError
from boundary.authorization.record import DirtyPathState, GitBaseline


@dataclass(frozen=True, slots=True)
class GitDelta:
    """One final Git snapshot compared with an authorization baseline."""

    head: str | None
    actual_paths: tuple[str, ...]
    dirty_path_states: tuple[DirtyPathState, ...]


def capture_git_delta(
    repository_root: str | Path,
    baseline: GitBaseline,
) -> GitDelta:
    """Derive final-state writes since authorization from exact Git state."""

    root = Path(repository_root)
    head_before = capture_git_head(root)
    dirty_states = capture_dirty_path_states(root)
    head_after = capture_git_head(root)
    if head_before != head_after:
        raise AuthorizationError(
            "Git HEAD changed while verification state was being captured"
        )

    baseline_by_path = {
        item.path: item.state
        for item in baseline.dirty_path_states
    }
    current_by_path = {
        item.path: item.state
        for item in dirty_states
    }
    candidates = sorted(
        set(baseline_by_path) | set(current_by_path)
    )
    actual: list[str] = []
    for path in candidates:
        current_state = current_by_path.get(path)
        if current_state is None:
            current_state = path_state(root, path)
        if baseline_by_path.get(path) != current_state:
            actual.append(path)

    return GitDelta(
        head=head_after,
        actual_paths=tuple(actual),
        dirty_path_states=dirty_states,
    )
