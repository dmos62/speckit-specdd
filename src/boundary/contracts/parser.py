"""Native Boundary contract parsing."""

from hashlib import sha256

from boundary.repository import normalize_repo_path

from .frontmatter import parse_frontmatter
from .model import Contract
from .sections import extract_contract_sections


def parse_contract(source: str, source_path: str) -> Contract:
    """Parse one canonical contract document without consulting filesystem state."""

    if not isinstance(source, str):
        raise TypeError("contract source must be a string")
    if not isinstance(source_path, str):
        raise TypeError("contract source path must be a string")

    normalized_source = source.replace("\r\n", "\n").replace("\r", "\n")
    normalized_source_path = normalize_repo_path(source_path)
    frontmatter, markdown = parse_frontmatter(normalized_source)
    sections = extract_contract_sections(markdown)
    identity = (
        f"sha256:{sha256(normalized_source.encode('utf-8')).hexdigest()}"
    )

    return Contract(
        contract_id=frontmatter.contract_id,
        source_path=normalized_source_path,
        owns=frontmatter.owns,
        applies_to=frontmatter.applies_to,
        depends_on=frontmatter.depends_on,
        sections=sections,
        content_identity=identity,
    )
