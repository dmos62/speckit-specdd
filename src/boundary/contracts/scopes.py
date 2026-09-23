"""Boundary v1 contract-scope validation."""

from boundary.repository import RepositoryPathError, normalize_repo_path

from .errors import ContractScopeError

_GLOB_TOKENS = ("*", "?", "[", "]", "{", "}")
_SUBTREE_SUFFIX = "/**"


def normalize_contract_scope(value: str) -> str:
    """Validate and return one canonical Boundary v1 scope.

    Supported scopes are exact repository-relative paths and subtree paths that
    end in ``/**``. Arbitrary glob syntax and the repository-wide ``**`` scope
    are rejected.
    """

    if not isinstance(value, str):
        raise TypeError("contract scope must be a string")
    if not value:
        raise ContractScopeError("contract scope must be non-empty")
    if value == "**":
        raise ContractScopeError("repository-wide '**' scope is not supported")

    is_subtree = value.endswith(_SUBTREE_SUFFIX)
    path_value = value[: -len(_SUBTREE_SUFFIX)] if is_subtree else value
    if not path_value:
        raise ContractScopeError("subtree scope must identify a repository path")
    if any(token in path_value for token in _GLOB_TOKENS):
        raise ContractScopeError("arbitrary glob syntax is not supported")

    try:
        normalized = normalize_repo_path(path_value)
    except RepositoryPathError as exc:
        raise ContractScopeError(str(exc)) from exc

    if normalized != path_value:
        raise ContractScopeError("contract scope must use canonical repository syntax")

    return f"{normalized}{_SUBTREE_SUFFIX}" if is_subtree else normalized
