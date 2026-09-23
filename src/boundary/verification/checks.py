"""Provider-neutral actual-write authorization checks."""

from pathlib import Path

from boundary.authorization import is_native_contract_path
from boundary.authorization.identities import effective_context_identity
from boundary.authorization.record import OperationRecord
from boundary.contracts import (
    ContractGraphError,
    ContractOwnershipError,
    ContractParseError,
    load_contract_graph,
)
from boundary.context import resolve_target_context

from .model import PathClassifier, PathKind, VerificationDiagnostic

_VALID_PATH_KINDS = {"ordinary", "change-system", "generated"}


def classify_actual_paths(
    current: OperationRecord,
    paths: tuple[str, ...],
    classifier: PathClassifier | None,
    diagnostics: list[VerificationDiagnostic],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Separate adapter-owned state without allowing it to hide core targets."""

    classify = classifier or _ordinary_path
    authorized = {
        target.path
        for target in current.authorized_targets
    }
    checked: list[str] = []
    excluded: list[str] = []
    for path in paths:
        if is_native_contract_path(path) or path in authorized:
            checked.append(path)
            continue
        try:
            kind = classify(path)
        except Exception as exc:
            diagnostics.append(
                diagnostic(
                    "INVALID_WRITE_TARGET",
                    f"path classifier failed for {path}: {exc}",
                    path,
                )
            )
            checked.append(path)
            continue
        if kind not in _VALID_PATH_KINDS:
            diagnostics.append(
                diagnostic(
                    "INVALID_WRITE_TARGET",
                    f"path classifier returned an unsupported kind for {path}",
                    path,
                )
            )
            checked.append(path)
        elif kind == "ordinary":
            checked.append(path)
        else:
            excluded.append(path)
    return tuple(checked), tuple(excluded)


def verify_checked_writes(
    repository_root: str | Path,
    current: OperationRecord,
    paths: tuple[str, ...],
) -> list[VerificationDiagnostic]:
    """Verify one operation kind without running feature convergence checks."""

    if current.kind == "implementation":
        return _verify_implementation_writes(
            repository_root,
            current,
            paths,
        )
    return _verify_contract_evolution_writes(current, paths)


def diagnostic(
    code: str,
    message: str,
    *paths: str,
) -> VerificationDiagnostic:
    """Build one stable product-level diagnostic."""

    return VerificationDiagnostic(
        code=code,
        message=message,
        paths=tuple(paths),
    )


def _verify_implementation_writes(
    repository_root: str | Path,
    current: OperationRecord,
    paths: tuple[str, ...],
) -> list[VerificationDiagnostic]:
    diagnostics: list[VerificationDiagnostic] = []
    authorized = {
        target.path: target
        for target in current.authorized_targets
    }
    project_paths: list[str] = []
    for path in paths:
        if is_native_contract_path(path):
            diagnostics.append(
                diagnostic(
                    "OPERATION_KIND_VIOLATION",
                    f"implementation operation modified native contract: {path}",
                    path,
                )
            )
            continue
        project_paths.append(path)
        if path not in authorized:
            diagnostics.append(
                diagnostic(
                    "UNDECLARED_WRITE",
                    f"actual implementation write was not authorized: {path}",
                    path,
                )
            )

    if not project_paths:
        return diagnostics
    try:
        graph = load_contract_graph(repository_root)
    except ContractOwnershipError as exc:
        diagnostics.append(
            diagnostic("AMBIGUOUS_OWNERSHIP", str(exc), *project_paths)
        )
        return diagnostics
    except (ContractParseError, ContractGraphError) as exc:
        diagnostics.append(
            diagnostic("CONTRACT_GRAPH_INVALID", str(exc), *project_paths)
        )
        return diagnostics

    for path in project_paths:
        try:
            context = resolve_target_context(graph, path)
        except ContractOwnershipError as exc:
            diagnostics.append(
                diagnostic("AMBIGUOUS_OWNERSHIP", str(exc), path)
            )
            continue
        if context.owner_id is None:
            diagnostics.append(
                diagnostic(
                    "UNOWNED_WRITE_TARGET",
                    f"actual implementation write has no primary owner: {path}",
                    path,
                )
            )
            continue

        evidence = authorized.get(path)
        if evidence is None:
            continue
        identity = effective_context_identity(graph, context)
        if (
            evidence.owner != context.owner_id
            or evidence.effective_context_identity != identity
        ):
            diagnostics.append(
                diagnostic(
                    "CONTRACT_CONTEXT_CHANGED",
                    f"effective contract context changed after authorization: {path}",
                    path,
                )
            )
    return diagnostics


def _verify_contract_evolution_writes(
    current: OperationRecord,
    paths: tuple[str, ...],
) -> list[VerificationDiagnostic]:
    authorized = {
        target.path
        for target in current.authorized_targets
    }
    diagnostics: list[VerificationDiagnostic] = []
    for path in paths:
        if not is_native_contract_path(path):
            diagnostics.append(
                diagnostic(
                    "OPERATION_KIND_VIOLATION",
                    f"contract-evolution operation modified project file: {path}",
                    path,
                )
            )
        elif path not in authorized:
            diagnostics.append(
                diagnostic(
                    "UNDECLARED_WRITE",
                    f"contract change was not authorized: {path}",
                    path,
                )
            )
    return diagnostics


def _ordinary_path(path: str) -> PathKind:
    del path
    return "ordinary"
