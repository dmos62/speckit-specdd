"""Boundary v1 contract-scope validation and matching."""

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
        raise ContractScopeError(
            "contract scope must use canonical repository syntax"
        )

    return f"{normalized}{_SUBTREE_SUFFIX}" if is_subtree else normalized


def scope_matches(scope: str, target_path: str) -> bool:
    """Return whether a canonical scope contains a repository target."""

    target = normalize_repo_path(target_path)
    if not scope.endswith(_SUBTREE_SUFFIX):
        return scope == target

    root = scope[: -len(_SUBTREE_SUFFIX)]
    return target == root or target.startswith(f"{root}/")


def scope_strictly_contains(outer: str, inner: str) -> bool:
    """Return whether one canonical scope is a strict superset of another."""

    if not outer.endswith(_SUBTREE_SUFFIX):
        return False

    outer_root = outer[: -len(_SUBTREE_SUFFIX)]
    if inner.endswith(_SUBTREE_SUFFIX):
        inner_root = inner[: -len(_SUBTREE_SUFFIX)]
        return inner_root.startswith(f"{outer_root}/")

    return scope_matches(outer, inner)


def scopes_overlap(left: str, right: str) -> bool:
    """Return whether two canonical Boundary scopes share at least one target."""

    left_subtree = left.endswith(_SUBTREE_SUFFIX)
    right_subtree = right.endswith(_SUBTREE_SUFFIX)

    if not left_subtree and not right_subtree:
        return left == right
    if left_subtree and not right_subtree:
        return scope_matches(left, right)
    if right_subtree and not left_subtree:
        return scope_matches(right, left)

    left_root = left[: -len(_SUBTREE_SUFFIX)]
    right_root = right[: -len(_SUBTREE_SUFFIX)]
    return (
        left_root == right_root
        or left_root.startswith(f"{right_root}/")
        or right_root.startswith(f"{left_root}/")
    )
