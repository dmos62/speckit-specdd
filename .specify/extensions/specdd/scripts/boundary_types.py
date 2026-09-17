from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class BoundaryError(RuntimeError):
    """The adapter cannot produce a valid Change Boundary."""


@dataclass(frozen=True)
class Target:
    raw: str
    path: str
    absolute_path: Path


@dataclass(frozen=True)
class Unresolved:
    input: str
    code: str
    message: str
    path: str | None = None
    candidate_authorities: tuple[str, ...] = ()


RunCommand = Callable[..., subprocess.CompletedProcess[str]]
