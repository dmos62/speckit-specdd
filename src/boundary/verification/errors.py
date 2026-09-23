"""Errors raised by native Boundary operation verification."""

from collections.abc import Sequence

from .model import VerificationDiagnostic


class VerificationError(RuntimeError):
    """Operation verification cannot produce trustworthy evidence."""

    def __init__(
        self,
        value: (
            str
            | VerificationDiagnostic
            | Sequence[VerificationDiagnostic]
        ),
    ) -> None:
        if isinstance(value, str):
            diagnostics: tuple[VerificationDiagnostic, ...] = ()
            message = value
        elif isinstance(value, VerificationDiagnostic):
            diagnostics = (value,)
            message = _render_diagnostics(diagnostics)
        else:
            diagnostics = tuple(value)
            message = _render_diagnostics(diagnostics)
        self.diagnostics = diagnostics
        super().__init__(message)

    @property
    def code(self) -> str | None:
        """Return the first provider-neutral diagnostic code, when present."""

        if not self.diagnostics:
            return None
        return self.diagnostics[0].code


def _render_diagnostics(
    diagnostics: tuple[VerificationDiagnostic, ...],
) -> str:
    if not diagnostics:
        return "operation verification failed"
    return "\n".join(
        f"{item.code}: {item.message}"
        for item in diagnostics
    )
