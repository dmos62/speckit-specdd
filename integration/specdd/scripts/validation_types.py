from __future__ import annotations

from dataclasses import dataclass


class ValidationError(RuntimeError):
    """Feature validation cannot produce a trustworthy result."""


@dataclass(frozen=True)
class TaskRecord:
    order: int
    task_id: str | None
    story: str | None
    text: str
    targets: tuple[str, ...]
    spec_targets: tuple[str, ...]
    invalid_targets: tuple[str, ...]
