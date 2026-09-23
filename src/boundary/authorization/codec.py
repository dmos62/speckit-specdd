"""Parsing for versioned native Boundary operation records."""

from collections.abc import Mapping

from .model import AuthorizationError, TaskWriteSet
from .record import (
    CarriedForwardState,
    DirtyPathState,
    GitBaseline,
    OperationRecord,
    OperationTargetEvidence,
)


def operation_record_from_document(
    value: object,
) -> OperationRecord:
    """Parse one version-1 operation document and fail closed on corruption."""

    root = _mapping(value, "operation record")
    if root.get("schemaVersion") != 1:
        raise AuthorizationError(
            "operation record must use schemaVersion 1"
        )

    try:
        tasks = tuple(
            _task(item)
            for item in _list(root.get("tasks"), "tasks")
        )
        targets = tuple(
            _target(item)
            for item in _list(
                root.get("authorizedTargets"),
                "authorizedTargets",
            )
        )
        baseline = _baseline(root.get("gitBaseline"))
        carried = tuple(
            _carried(item)
            for item in _list(
                root.get("carriedForward", []),
                "carriedForward",
            )
        )
        status = _string(root.get("status"), "status")
        final_states = _verification_states(
            root.get("verification"),
            status,
        )
        return OperationRecord(
            operation_id=_string(
                root.get("operationId"),
                "operationId",
            ),
            change_id=_string(root.get("changeId"), "changeId"),
            kind=_string(root.get("kind"), "kind"),
            tasks=tasks,
            authorized_targets=targets,
            contract_graph_identity=_string(
                root.get("contractGraphIdentity"),
                "contractGraphIdentity",
            ),
            git_baseline=baseline,
            carried_forward=carried,
            verification_final_states=final_states,
            status=status,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, AuthorizationError):
            raise
        raise AuthorizationError(
            f"invalid operation record: {exc}"
        ) from exc


def _task(value: object) -> TaskWriteSet:
    item = _mapping(value, "task")
    order = item.get("order")
    if isinstance(order, bool) or not isinstance(order, int):
        raise AuthorizationError("task order must be an integer")
    return TaskWriteSet(
        order=order,
        task_id=_optional_string(item.get("id"), "task id"),
        story=_optional_string(item.get("story"), "task story"),
        writes=tuple(
            _string(write, "task write")
            for write in _list(item.get("writes"), "task writes")
        ),
    )


def _target(value: object) -> OperationTargetEvidence:
    item = _mapping(value, "authorized target")
    return OperationTargetEvidence(
        path=_string(item.get("path"), "authorized target path"),
        owner=_optional_string(item.get("owner"), "target owner"),
        effective_context_identity=_optional_string(
            item.get("effectiveContextIdentity"),
            "effective context identity",
        ),
    )


def _baseline(value: object) -> GitBaseline:
    item = _mapping(value, "gitBaseline")
    head = item.get("head")
    if head is not None:
        head = _string(head, "gitBaseline head")
    return GitBaseline(
        head=head,
        dirty_path_states=tuple(
            _dirty_state(state)
            for state in _list(
                item.get("dirtyPathStates"),
                "dirtyPathStates",
            )
        ),
    )


def _dirty_state(value: object) -> DirtyPathState:
    item = _mapping(value, "path state")
    return DirtyPathState(
        path=_string(item.get("path"), "path state path"),
        state=_string(item.get("state"), "path state identity"),
    )


def _carried(value: object) -> CarriedForwardState:
    item = _mapping(value, "carried-forward state")
    return CarriedForwardState(
        path=_string(item.get("path"), "carried-forward path"),
        state=_string(item.get("state"), "carried-forward state"),
        operation_id=_string(
            item.get("operationId"),
            "predecessor operation id",
        ),
    )


def _verification_states(
    value: object,
    status: str,
) -> tuple[DirtyPathState, ...]:
    if status == "authorized":
        if value is not None:
            raise AuthorizationError(
                "authorized operation must not contain verification evidence"
            )
        return ()
    item = _mapping(value, "verification")
    return tuple(
        _dirty_state(state)
        for state in _list(
            item.get("finalPathStates"),
            "verification finalPathStates",
        )
    )


def _mapping(
    value: object,
    label: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AuthorizationError(f"{label} must be an object")
    return value


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise AuthorizationError(f"{label} must be an array")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"{label} must be a non-empty string")
    return value


def _optional_string(
    value: object,
    label: str,
) -> str | None:
    if value is None:
        return None
    return _string(value, label)
