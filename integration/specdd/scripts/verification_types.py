from __future__ import annotations

from dataclasses import dataclass


class VerificationError(RuntimeError):
    """Actual-change verification cannot produce a trustworthy result."""


IMMUTABLE_BOOTSTRAP_CONTROL = ".specdd/bootstrap.md"
PROJECT_BOOTSTRAP_CONTROL = ".specdd/bootstrap.project.md"
LOCAL_BOOTSTRAP_CONTROL = ".specdd/bootstrap.local.md"
EDITABLE_BOOTSTRAP_CONTROLS = frozenset(
    {
        PROJECT_BOOTSTRAP_CONTROL,
        LOCAL_BOOTSTRAP_CONTROL,
    }
)
CONTROL_SELECTION_SOURCES = frozenset({"operator", "workflow"})
_GENERATED_PREFIXES = (".specify/", ".specify-agent/")
_GENERATED_EXACT = frozenset({LOCAL_BOOTSTRAP_CONTROL})
_CODEX_SKILL_ROOT = ".agents/skills/"
_CODEX_SKILL_PREFIX = "speckit-"


def is_generated_path(path: str) -> bool:
    if path in _GENERATED_EXACT or any(
        path.startswith(prefix)
        for prefix in _GENERATED_PREFIXES
    ):
        return True
    if not path.startswith(_CODEX_SKILL_ROOT):
        return False

    skill_path = path[len(_CODEX_SKILL_ROOT):]
    skill_name, separator, _ = skill_path.partition("/")
    return bool(
        separator
        and skill_name.startswith(_CODEX_SKILL_PREFIX)
    )


@dataclass(frozen=True)
class GitChange:
    path: str
    status: str
    deleted: bool = False


@dataclass(frozen=True)
class ChangeSet:
    writes: tuple[GitChange, ...] = ()
    specs: tuple[GitChange, ...] = ()
    controls: tuple[GitChange, ...] = ()
    feature_artifacts: tuple[GitChange, ...] = ()
    generated: tuple[GitChange, ...] = ()
    preauthorization: tuple[GitChange, ...] = ()
