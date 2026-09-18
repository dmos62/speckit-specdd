from __future__ import annotations

from dataclasses import dataclass


class VerificationError(RuntimeError):
    """Actual-change verification cannot produce a trustworthy result."""


IMMUTABLE_BOOTSTRAP_CONTROL = ".specdd/bootstrap.md"
PROJECT_BOOTSTRAP_CONTROL = ".specdd/bootstrap.project.md"
LOCAL_BOOTSTRAP_CONTROL = ".specdd/bootstrap.local.md"
EDITABLE_BOOTSTRAP_CONTROLS = frozenset(
    {
        PROJECT_BOOTSTRAP_CONTROL,
        LOCAL_BOOTSTRAP_CONTROL,
    }
)
CONTROL_SELECTION_SOURCES = frozenset({"operator", "workflow"})


@dataclass(frozen=True)
class GitChange:
    path: str
    status: str
    deleted: bool = False


@dataclass(frozen=True)
class ChangeSet:
    writes: tuple[GitChange, ...] = ()
    specs: tuple[GitChange, ...] = ()
    controls: tuple[GitChange, ...] = ()
    feature_artifacts: tuple[GitChange, ...] = ()
    generated: tuple[GitChange, ...] = ()
