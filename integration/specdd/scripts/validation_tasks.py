from __future__ import annotations

import re
from pathlib import Path

from boundary_types import BoundaryError
from validation_task_paths import (
    extract_repository_targets,
    inline_code_matches,
    is_specdd_control_path,
    mask_ranges,
    normalize_task_target,
)
from validation_types import (
    EVOLUTION_CLASSIFICATIONS,
    TaskRecord,
    diagnostic,
    task_fields,
)

_TASK_RE = re.compile(r"^\s*-\s+\[(?: |x|X|-|!|\?)\]\s+(?P<body>.+?)\s*$")
_TASK_ID_RE = re.compile(r"^(?P<id>T\d+)\b")
_STORY_RE = re.compile(r"\[(?P<story>US\d+)\]")
_WRITES_RE = re.compile(r"^[ \t]+Writes:[ \t]*(?P<body>.*?)\s*$")
_EVOLUTION_RE = re.compile(
    r"\b(?:" + "|".join(EVOLUTION_CLASSIFICATIONS) + r")\b"
)


def _parse_writes(
    root: Path,
    value: str,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    matches = inline_code_matches(value)
    errors: list[str] = []
    invalid: list[str] = []
    ordinary: list[str] = []
    specs: list[str] = []
    controls: list[str] = []

    if not value.strip():
        return (), (), (), (), ("Writes metadata must declare at least one path",)
    if not matches:
        return (), (), (), (), ("Writes metadata must use backticked exact paths",)

    remainder = mask_ranges(value, [match.span() for match in matches])
    if remainder.replace(",", "").strip():
        errors.append(
            "Writes metadata must contain only comma-separated backticked paths"
        )

    seen: set[str] = set()
    for match in matches:
        raw = match.group(1).strip()
        try:
            normalized = normalize_task_target(root, raw, literal=True)
        except BoundaryError:
            invalid.append(raw or "<empty>")
            continue
        if normalized in seen:
            errors.append(f"duplicate declared write target: {normalized}")
            continue
        seen.add(normalized)
        if is_specdd_control_path(normalized):
            controls.append(normalized)
        elif normalized.lower().endswith(".sdd"):
            specs.append(normalized)
        else:
            ordinary.append(normalized)
    return (
        tuple(ordinary),
        tuple(specs),
        tuple(controls),
        tuple(invalid),
        tuple(errors),
    )


def parse_tasks(root: Path, text: str) -> list[TaskRecord]:
    tasks: list[TaskRecord] = []
    current: dict[str, object] | None = None
    metadata_open = False

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        tasks.append(
            TaskRecord(
                order=len(tasks),
                task_id=current["task_id"],
                story=current["story"],
                text=current["text"],
                targets=tuple(current["targets"]),
                spec_targets=tuple(current["spec_targets"]),
                invalid_targets=tuple(current["invalid_targets"]),
                control_targets=tuple(current["control_targets"]),
                evolution_markers=tuple(current["evolution_markers"]),
                writes_declared=bool(current["writes_declared"]),
                write_metadata_errors=tuple(current["write_metadata_errors"]),
            )
        )
        current = None

    for line in text.splitlines():
        task_match = _TASK_RE.match(line)
        if task_match is not None:
            flush()
            body = task_match.group("body")
            task_id_match = _TASK_ID_RE.match(body)
            story_match = _STORY_RE.search(body)
            current = {
                "task_id": task_id_match.group("id") if task_id_match else None,
                "story": story_match.group("story") if story_match else None,
                "text": body,
                "targets": [],
                "spec_targets": [],
                "invalid_targets": [],
                "control_targets": [],
                "evolution_markers": list(dict.fromkeys(_EVOLUTION_RE.findall(body))),
                "writes_declared": False,
                "write_metadata_errors": [],
            }
            metadata_open = True
            continue

        if current is None or not metadata_open:
            continue
        writes_match = _WRITES_RE.match(line)
        if writes_match is not None:
            if current["writes_declared"]:
                current["write_metadata_errors"].append("duplicate Writes metadata")
                continue
            current["writes_declared"] = True
            ordinary, specs, controls, invalid, errors = _parse_writes(
                root,
                writes_match.group("body"),
            )
            current["targets"].extend(ordinary)
            current["spec_targets"].extend(specs)
            current["control_targets"].extend(controls)
            current["invalid_targets"].extend(invalid)
            current["write_metadata_errors"].extend(errors)
            continue
        if line.strip():
            metadata_open = False

    flush()
    return tasks


def project_evolution(
    task: TaskRecord,
    *,
    severity: str,
) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    markers = list(dict.fromkeys(task.evolution_markers))
    if not markers:
        return None, []
    diagnostics: list[dict[str, object]] = []
    if len(markers) > 1:
        diagnostics.append(
            diagnostic(
                "EVOLUTION_CLASSIFICATION_CONFLICT",
                severity,
                "Task declares more than one SpecDD evolution class.",
                evolutionClassifications=markers,
                **task_fields(task),
            )
        )
        return {
            "classification": None,
            "markers": markers,
            "specTargets": list(task.spec_targets),
            "requiresFreshBoundary": True,
            "endsAuthorityContext": True,
        }, diagnostics

    classification = markers[0]
    if task.targets or task.control_targets:
        diagnostics.append(
            diagnostic(
                "EVOLUTION_SCOPE_MIXED",
                severity,
                "SpecDD evolution must remain separate from implementation "
                "and bootstrap-control writes.",
                targets=list(task.targets),
                controlTargets=list(task.control_targets),
                evolutionClassification=classification,
                **task_fields(task),
            )
        )
    if not task.spec_targets:
        diagnostics.append(
            diagnostic(
                "EVOLUTION_SPEC_TARGET_REQUIRED",
                severity,
                "SpecDD evolution must name at least one .sdd target in Writes metadata.",
                evolutionClassification=classification,
                **task_fields(task),
            )
        )
    return {
        "classification": classification,
        "specTargets": list(task.spec_targets),
        "requiresFreshBoundary": True,
        "endsAuthorityContext": classification == "AUTHORITY_EVOLUTION_REQUIRED",
    }, diagnostics


def parse_tasks_file(root: Path, path: Path) -> list[TaskRecord]:
    return parse_tasks(root, path.read_text(encoding="utf-8"))


__all__ = [
    "extract_repository_targets",
    "is_specdd_control_path",
    "parse_tasks",
    "parse_tasks_file",
    "project_evolution",
]
