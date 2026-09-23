"""Effective target-context projection boundary."""

from .model import ProvenancedText, TargetContext
from .resolver import resolve_target_context

__all__ = [
    "ProvenancedText",
    "TargetContext",
    "resolve_target_context",
]
