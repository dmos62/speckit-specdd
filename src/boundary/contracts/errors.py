"""Errors raised while loading native Boundary contracts."""


class ContractParseError(ValueError):
    """Raised when a canonical contract cannot be parsed deterministically."""


class ContractScopeError(ContractParseError):
    """Raised when a contract declares an unsupported repository scope."""
