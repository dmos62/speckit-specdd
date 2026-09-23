"""Extraction of recognized native contract Markdown sections."""

import re

from .errors import ContractParseError
from .model import ContractSections

_HEADING_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*#*[ \t]*$")
_ITEM_RE = re.compile(r"^[ \t]*[-*+][ \t]+(.+?)\s*$")
_RECOGNIZED = {"Purpose", "Invariants", "Prohibitions", "Interfaces"}


def extract_contract_sections(markdown: str) -> ContractSections:
    """Extract recognized level-two semantic sections from contract Markdown."""

    collected: dict[str, list[str]] = {}
    current: str | None = None
    for line in markdown.split("\n"):
        heading = _HEADING_RE.match(line)
        if heading is not None:
            title = heading.group(1).strip()
            current = title if title in _RECOGNIZED else None
            if current is not None:
                if current in collected:
                    raise ContractParseError(
                        f"duplicate semantic section {current!r}"
                    )
                collected[current] = []
            continue
        if current is not None:
            collected[current].append(line)

    purpose_text = _section_text(collected.get("Purpose", []))
    return ContractSections(
        purpose=purpose_text or None,
        invariants=_section_items(collected.get("Invariants", [])),
        prohibitions=_section_items(collected.get("Prohibitions", [])),
        interfaces=_section_items(collected.get("Interfaces", [])),
    )


def _section_text(lines: list[str]) -> str:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def _section_items(lines: list[str]) -> tuple[str, ...]:
    items: list[str] = []
    current: list[str] = []

    def flush() -> None:
        text = " ".join(
            part.strip()
            for part in current
            if part.strip()
        ).strip()
        if text:
            items.append(text)
        current.clear()

    for line in lines:
        item_match = _ITEM_RE.match(line)
        if item_match is not None:
            flush()
            current.append(item_match.group(1))
            continue
        if not line.strip():
            flush()
            continue
        current.append(line)
    flush()
    return tuple(items)
