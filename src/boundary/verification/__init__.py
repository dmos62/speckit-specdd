"""Provider-neutral actual-write verification boundary."""

from .errors import VerificationError
from .model import (
    PathClassifier,
    PathKind,
    VerificationDiagnostic,
    VerificationResult,
)
from .service import (
    finalize_operation_verification,
    verify_operation_authorization,
)

__all__ = [
    "PathClassifier",
    "PathKind",
    "VerificationDiagnostic",
    "VerificationError",
    "VerificationResult",
    "finalize_operation_verification",
    "verify_operation_authorization",
]
