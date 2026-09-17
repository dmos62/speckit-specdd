from __future__ import annotations

from dataclasses import dataclass


class VerificationError(RuntimeError):
    """Actual-change verification cannot produce a trustworthy result."""


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
