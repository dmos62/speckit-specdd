#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TARGET_ROOT = Path(".agents") / "skills"
SKILLS = (
    (
        "boundary-scope",
        "scope",
        "Plan exact Boundary write scope and inspect effective contract context.",
    ),
    (
        "boundary-implement",
        "implement",
        "Implement only within a successful Boundary authorization.",
    ),
    (
        "boundary-contracts",
        "contracts",
        "Evolve persistent Boundary contracts as a separate operation.",
    ),
)


def _canonical_bytes(source_root: Path, source_name: str) -> bytes:
    path = source_root / "skills" / source_name / "SKILL.md"
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(
            f"canonical Boundary skill is unavailable: {path}: {error}"
        )
    if not content.endswith("\n"):
        content += "\n"
    return content.encode("utf-8")


def _render(
    source_root: Path,
    name: str,
    source_name: str,
    description: str,
) -> bytes:
    frontmatter = (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
    ).encode("utf-8")
    return frontmatter + _canonical_bytes(source_root, source_name)


def _target(project_root: Path, name: str) -> Path:
    return project_root / TARGET_ROOT / name / "SKILL.md"


def materialize(source_root: Path, project_root: Path) -> None:
    for name, source_name, description in SKILLS:
        target = _target(project_root, name)
        payload = _render(source_root, name, source_name, description)
        if target.is_file() and target.read_bytes() == payload:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(".SKILL.md.tmp")
        temporary.write_bytes(payload)
        temporary.replace(target)


def check(source_root: Path, project_root: Path) -> None:
    stale = []
    for name, source_name, description in SKILLS:
        target = _target(project_root, name)
        expected = _render(source_root, name, source_name, description)
        if not target.is_file() or target.read_bytes() != expected:
            stale.append(target.as_posix())
    if stale:
        raise SystemExit(
            "Codex Boundary skill materialization is missing or stale: "
            + ", ".join(stale)
        )


def remove(project_root: Path) -> None:
    for name, _, _ in SKILLS:
        target_dir = _target(project_root, name).parent
        if target_dir.exists():
            shutil.rmtree(target_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path("."))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    project_root = args.project_root.resolve()
    if args.remove:
        remove(project_root)
    elif args.check:
        check(source_root, project_root)
    else:
        materialize(source_root, project_root)


if __name__ == "__main__":
    main()
