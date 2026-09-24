"""Immutable downstream Boundary lock parsing and source materialization."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import urllib.error
import urllib.request

_SCHEMA = "boundary.lock/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_GITHUB_COMMIT_ARCHIVE_RE = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/archive/"
    r"(?P<revision>[0-9a-fA-F]{40})\.(?P<kind>zip|tar\.gz|tgz)$"
)
_REQUIRED_SOURCE_PATHS = (
    "integration/speckit/extension.yml",
    "integration/speckit-preset/preset.yml",
    "integration/speckit/workflow-overlay.yml",
    "adapters/codex/materialize.py",
    "scripts/install.sh",
    "scripts/install-host.sh",
    "scripts/install-source.sh",
    "scripts/consumer.py",
    "scripts/consumer_lock.py",
    "src/boundary/__init__.py",
    "skills/scope/SKILL.md",
    "skills/implement/SKILL.md",
    "skills/contracts/SKILL.md",
)


class BoundaryLockError(ValueError):
    """Raised when immutable Boundary source evidence is invalid."""


@dataclass(frozen=True, slots=True)
class BoundaryLock:
    """One immutable Boundary source archive identity."""

    source_url: str
    revision: str
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_url, str) or not self.source_url:
            raise BoundaryLockError("source url must be a non-empty string")
        if not isinstance(self.revision, str):
            raise BoundaryLockError("source revision must be a string")
        if not isinstance(self.sha256, str):
            raise BoundaryLockError("source sha256 must be a string")

        revision = self.revision.lower()
        digest = self.sha256.lower()
        if _REVISION_RE.fullmatch(revision) is None:
            raise BoundaryLockError(
                "source revision must be a 40-character Git commit id"
            )
        if _SHA256_RE.fullmatch(digest) is None:
            raise BoundaryLockError(
                "source sha256 must be a 64-character hexadecimal digest"
            )

        match = _GITHUB_COMMIT_ARCHIVE_RE.fullmatch(self.source_url)
        if match is None:
            raise BoundaryLockError(
                "source url must be an immutable HTTPS GitHub commit archive"
            )
        if match.group("revision").lower() != revision:
            raise BoundaryLockError(
                "source url revision does not match source revision"
            )

        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "sha256", digest)

    def to_document(self) -> dict[str, object]:
        """Return the stable downstream lock document."""

        return {
            "schema": _SCHEMA,
            "source": {
                "url": self.source_url,
                "revision": self.revision,
                "sha256": self.sha256,
            },
        }


def load_lock(path: str | Path) -> BoundaryLock:
    """Load and strictly validate one committed Boundary lock."""

    lock_path = Path(path)
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BoundaryLockError(
            f"Boundary lock is invalid JSON: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise BoundaryLockError("Boundary lock must be a JSON object")
    if set(value) != {"schema", "source"}:
        raise BoundaryLockError(
            "Boundary lock must contain only schema and source"
        )
    if value["schema"] != _SCHEMA:
        raise BoundaryLockError(
            f"Boundary lock schema must be {_SCHEMA!r}"
        )

    source = value["source"]
    if not isinstance(source, dict):
        raise BoundaryLockError("Boundary lock source must be an object")
    expected = {"url", "revision", "sha256"}
    if set(source) != expected:
        raise BoundaryLockError(
            "Boundary lock source must contain only url, revision, and sha256"
        )
    if not all(isinstance(source[key], str) for key in expected):
        raise BoundaryLockError(
            "Boundary lock source values must be strings"
        )

    return BoundaryLock(
        source_url=source["url"],
        revision=source["revision"],
        sha256=source["sha256"],
    )


def write_lock(path: str | Path, lock: BoundaryLock) -> None:
    """Atomically replace a downstream Boundary lock."""

    output = Path(path)
    rendered = (
        json.dumps(
            lock.to_document(),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=output.name + ".",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        temporary.replace(output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def materialize_locked_source(
    lock: BoundaryLock,
    destination: str | Path,
) -> Path:
    """Download, verify, and extract exactly the source named by a lock."""

    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    archive = root / _archive_name(lock.source_url)
    _download(lock.source_url, archive)

    actual = _sha256_file(archive)
    if actual != lock.sha256:
        raise BoundaryLockError(
            "Boundary source checksum mismatch: "
            f"expected {lock.sha256}, received {actual}"
        )

    extracted = root / "extracted"
    extracted.mkdir()
    try:
        shutil.unpack_archive(str(archive), str(extracted))
    except (OSError, shutil.ReadError, ValueError) as exc:
        raise BoundaryLockError(
            f"Boundary source archive could not be extracted: {exc}"
        ) from exc

    source_root = _single_archive_root(extracted)
    _require_source_tree(source_root)
    return source_root


def _download(url: str, output: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Boundary locked consumer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with output.open("wb") as handle:
                shutil.copyfileobj(response, handle)
    except (OSError, urllib.error.URLError) as exc:
        raise BoundaryLockError(
            f"Boundary source archive could not be downloaded: {exc}"
        ) from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_name(url: str) -> str:
    if url.endswith(".tar.gz"):
        return "source.tar.gz"
    if url.endswith(".tgz"):
        return "source.tgz"
    if url.endswith(".zip"):
        return "source.zip"
    raise BoundaryLockError("unsupported Boundary source archive format")


def _single_archive_root(extracted: Path) -> Path:
    entries = tuple(extracted.iterdir())
    if len(entries) != 1 or not entries[0].is_dir():
        raise BoundaryLockError(
            "Boundary source archive must contain one top-level directory"
        )
    return entries[0]


def _require_source_tree(source_root: Path) -> None:
    missing = [
        path
        for path in _REQUIRED_SOURCE_PATHS
        if not (source_root / path).is_file()
    ]
    if missing:
        raise BoundaryLockError(
            "Boundary source archive is incomplete: " + ", ".join(missing)
        )
