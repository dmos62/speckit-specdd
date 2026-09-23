"""Provider-neutral target-context data structures."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProvenancedText:
    """One projected semantic item with its canonical source."""

    text: str
    contract_id: str
    source_path: str
    section: str
    content_identity: str = ""


@dataclass(frozen=True, slots=True)
class TargetContext:
    """Disposable effective contract context for one repository target."""

    target_path: str
    owner_id: str | None
    applicable_contract_ids: tuple[str, ...] = ()
    purposes: tuple[ProvenancedText, ...] = ()
    invariants: tuple[ProvenancedText, ...] = ()
    prohibitions: tuple[ProvenancedText, ...] = ()
    dependency_interfaces: tuple[ProvenancedText, ...] = ()
    interfaces: tuple[ProvenancedText, ...] = ()
