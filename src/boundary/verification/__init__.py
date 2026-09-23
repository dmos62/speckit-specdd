"""Provider-neutral actual-write verification boundary."""

from .errors import VerificationError
from .service import finalize_operation_verification

__all__ = [
    "VerificationError",
    "finalize_operation_verification",
]
