"""Structured change-adapter write declarations."""

from dataclasses import dataclass

from boundary.repository import RepositoryPathError, normalize_repo_path


class WriteSetError(ValueError):
    """Raised when a change adapter supplies an invalid declared write set."""


@dataclass(frozen=True, slots=True)
class TaskWriteSet:
    """Canonical task identity plus its exact ordered implementation writes."""

    order: int
    task_id: str | None
    story: str | None
    writes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.order, bool) or not isinstance(self.order, int):
            raise TypeError("task order must be an integer")
        if self.order < 0:
            raise WriteSetError("task order must be non-negative")
        _validate_optional_identity(self.task_id, "task id")
        _validate_optional_identity(self.story, "task story")

        writes = tuple(self.writes)
        normalized: list[str] = []
        seen: set[str] = set()
        for write in writes:
            if not isinstance(write, str):
                raise TypeError("declared write targets must be strings")
            try:
                canonical = normalize_repo_path(write)
            except RepositoryPathError as exc:
                raise WriteSetError(str(exc)) from exc
            if canonical != write:
                raise WriteSetError(
                    "declared write target must use canonical repository syntax: "
                    f"{write!r}"
                )
            if write in seen:
                raise WriteSetError(
                    f"declared write target is duplicated: {write!r}"
                )
            seen.add(write)
            normalized.append(write)
        object.__setattr__(self, "writes", tuple(normalized))


@dataclass(frozen=True, slots=True)
class ChangeWriteSet:
    """Ordered task write declarations supplied by one change-system adapter."""

    change_id: str
    tasks: tuple[TaskWriteSet, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.change_id, str):
            raise TypeError("change id must be a string")
        if not self.change_id.strip():
            raise WriteSetError("change id must be non-empty")

        tasks = tuple(self.tasks)
        orders = tuple(task.order for task in tasks)
        if len(orders) != len(set(orders)):
            raise WriteSetError("task orders must be unique")
        if orders != tuple(sorted(orders)):
            raise WriteSetError("tasks must preserve canonical task order")

        task_ids = [task.task_id for task in tasks if task.task_id is not None]
        if len(task_ids) != len(set(task_ids)):
            raise WriteSetError("task ids must be unique when present")
        object.__setattr__(self, "tasks", tasks)

    @property
    def writes(self) -> tuple[str, ...]:
        """Return the ordered union of all exact task writes."""

        result: list[str] = []
        seen: set[str] = set()
        for task in self.tasks:
            for write in task.writes:
                if write not in seen:
                    seen.add(write)
                    result.append(write)
        return tuple(result)


def _validate_optional_identity(value: str | None, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string or None")
    if not value.strip():
        raise WriteSetError(f"{label} must be non-empty when present")
