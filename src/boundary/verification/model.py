"""Provider-neutral results and path classification for native verification."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from boundary.authorization.record import DirtyPathState, OperationRecord

PathKind = Literal["ordinary", "change-system", "generated"]
PathClassifier = Callable[[str], PathKind]


@dataclass(frozen=True, slots=True)
class VerificationDiagnostic:
    """One provider-neutral authorization-verification finding."""

    code: str
    message: str
    paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Deterministic verification projection before epoch closure."""

    operation: OperationRecord
    actual_paths: tuple[str, ...] = ()
    checked_writes: tuple[str, ...] = ()
    excluded_paths: tuple[str, ...] = ()
    dirty_path_states: tuple[DirtyPathState, ...] = ()
    diagnostics: tuple[VerificationDiagnostic, ...] = ()

    @property
    def blocking(self) -> bool:
        """Return whether authorization verification found any violation."""

        return bool(self.diagnostics)
