"""Errors raised while loading native Boundary contracts."""


class ContractParseError(ValueError):
    """Raised when a canonical contract cannot be parsed deterministically."""


class ContractScopeError(ContractParseError):
    """Raised when a contract declares an unsupported repository scope."""


class ContractGraphError(ValueError):
    """Raised when parsed contracts cannot form one valid contract graph."""


class ContractOwnershipError(ContractGraphError):
    """Raised when ownership cannot be ordered unambiguously."""


class ContractDependencyError(ContractGraphError):
    """Raised when a declared direct dependency is invalid."""
