"""Structured native authorization inputs and resolved authority projections."""

from dataclasses import dataclass

from boundary.repository import RepositoryPathError, normalize_repo_path


class WriteSetError(ValueError):
    """Raised when a change adapter supplies an invalid declared write set."""


class AuthorizationError(ValueError):
    """Raised when canonical inputs cannot authorize an operation."""


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
        object.__setattr__(
            self,
            "writes",
            _canonical_writes(
                self.writes,
                label="declared write target",
            ),
        )


@dataclass(frozen=True, slots=True)
class ChangeWriteSet:
    """Ordered implementation writes supplied by one change-system adapter."""

    change_id: str
    tasks: tuple[TaskWriteSet, ...] = ()

    def __post_init__(self) -> None:
        _validate_change_id(self.change_id)

        tasks = tuple(self.tasks)
        orders = tuple(task.order for task in tasks)
        if len(orders) != len(set(orders)):
            raise WriteSetError("task orders must be unique")
        if orders != tuple(sorted(orders)):
            raise WriteSetError("tasks must preserve canonical task order")

        task_ids = [task.task_id for task in tasks if task.task_id is not None]
        if len(task_ids) != len(set(task_ids)):
            raise WriteSetError("task ids must be unique when present")

        declared_by: dict[str, int] = {}
        for task in tasks:
            for write in task.writes:
                previous = declared_by.get(write)
                if previous is not None:
                    raise WriteSetError(
                        "declared write target appears in multiple tasks: "
                        f"{write!r} (task orders {previous} and {task.order})"
                    )
                declared_by[write] = task.order

        object.__setattr__(self, "tasks", tasks)

    @property
    def writes(self) -> tuple[str, ...]:
        """Return all exact task writes in canonical task order."""

        return tuple(
            write
            for task in self.tasks
            for write in task.writes
        )


@dataclass(frozen=True, slots=True)
class ContractEvolutionWriteSet:
    """Exact native contract targets for a separate contract-evolution operation."""

    change_id: str
    writes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_change_id(self.change_id)
        object.__setattr__(
            self,
            "writes",
            _canonical_writes(
                self.writes,
                label="contract-evolution target",
            ),
        )


@dataclass(frozen=True, slots=True)
class AuthorizedTarget:
    """One implementation target resolved against fresh canonical contracts."""

    path: str
    owner_id: str
    effective_context_identity: str


@dataclass(frozen=True, slots=True)
class ImplementationAuthorization:
    """Fresh canonical authorization result for one implementation operation."""

    change_id: str
    tasks: tuple[TaskWriteSet, ...]
    targets: tuple[AuthorizedTarget, ...]
    contract_graph_identity: str

    @property
    def writes(self) -> tuple[str, ...]:
        """Return exact authorized implementation paths in canonical order."""

        return tuple(target.path for target in self.targets)


@dataclass(frozen=True, slots=True)
class ContractEvolutionAuthorization:
    """Fresh canonical authorization result for contract evolution only."""

    change_id: str
    targets: tuple[str, ...]
    contract_graph_identity: str


def _canonical_writes(
    writes: tuple[str, ...],
    *,
    label: str,
) -> tuple[str, ...]:
    values = tuple(writes)
    normalized: list[str] = []
    seen: set[str] = set()
    for write in values:
        if not isinstance(write, str):
            raise TypeError(f"{label}s must be strings")
        try:
            canonical = normalize_repo_path(write)
        except RepositoryPathError as exc:
            raise WriteSetError(str(exc)) from exc
        if canonical != write:
            raise WriteSetError(
                f"{label} must use canonical repository syntax: {write!r}"
            )
        if write in seen:
            raise WriteSetError(f"{label} is duplicated: {write!r}")
        seen.add(write)
        normalized.append(write)
    return tuple(normalized)


def _validate_change_id(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("change id must be a string")
    if not value.strip():
        raise WriteSetError("change id must be non-empty")


def _validate_optional_identity(value: str | None, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string or None")
    if not value.strip():
        raise WriteSetError(f"{label} must be non-empty when present")
