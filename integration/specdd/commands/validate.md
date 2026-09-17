---
description: Validate the active feature's Spec Kit tasks against the current SpecDD Change Boundary.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input before validation. The optional lifecycle stage may be `planning`, `tasks`, or
`implementation`. Default to `tasks`.

## Goal

Validate concrete Spec Kit task write targets against the active feature's derived SpecDD Change Boundary. Deterministic
path and authority mechanics belong to the bridge validation script. Architectural classification remains an agentic
responsibility where the deterministic result cannot decide intent.

This command never rewrites tasks, edits `.sdd` files, or relaxes SpecDD authority.

## Execution

1. From the repository root, run:

       .specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly

   Parse `FEATURE_DIR` from the JSON result. If the command fails or no active feature is available, stop and instruct
   the user to create or select a feature with `/speckit.specify`.

2. Resolve the repository root with:

       git rev-parse --show-toplevel

   Treat that path as the bridge root. `FEATURE_DIR` must resolve inside it. Stop if the active feature is outside the
   repository root.

3. Derive:
   - `FEATURE_ID` as the basename of `FEATURE_DIR`.
   - `BOUNDARY_FILE` as `FEATURE_DIR/.specdd/boundary.json`.
   - `TASK_FILE` as `FEATURE_DIR/tasks.md`.

4. Require both current inputs:
   - If `BOUNDARY_FILE` does not exist, stop and instruct the user to run `/speckit.specdd.context`.
   - If `TASK_FILE` does not exist, stop and instruct the user to generate tasks with `/speckit.tasks`.

5. Select validation strictness:
   - `planning`: unresolved scope is advisory while concrete implementation paths may still be emerging.
   - `tasks`: unresolved or stale task scope is an error that must be corrected before implementation planning is
     considered complete.
   - `implementation`: stale scope blocks, and unknown or conflicting write authority produces a blocking
     `AUTHORITY_VIOLATION`.
   - If `$ARGUMENTS` does not select a stage, use `tasks`.

6. Run the deterministic validator:

       uv run --no-project python integration/specdd/scripts/validation.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --boundary "<feature-dir>/.specdd/boundary.json" \
         --tasks "<feature-dir>/tasks.md" \
         --stage "<stage>"

   Do not parse `.sdd` files, derive ownership independently, or repair the Change Boundary by hand.

7. Interpret deterministic diagnostics:
   - `UNRESOLVED_TARGET`: a boundary or task target does not currently have trustworthy authority projection.
   - `MULTI_AUTHORITY_TASK`: one task writes targets owned by more than one primary authority. This is a structural
     finding, not automatic invalidity.
   - `STALE_BOUNDARY`: current task targets or feature identity no longer match the boundary projection.
   - `AUTHORITY_VIOLATION`: implementation-stage authority is unresolved or conflicting and implementation must not
     proceed.

8. Preserve Spec Kit task identity:
   - Keep original task order.
   - Keep the original task ID as the anchor when discussing decomposition.
   - Keep the original user-story grouping.
   - Do not rewrite `tasks.md` automatically.
   - When a `MULTI_AUTHORITY_TASK` is naturally decomposable, recommend authority-local sub-work using the validator's
     `authorityGroups`, while keeping the work under the same feature and user story.

9. Apply architectural classification only where reasoning is required:
   - Use `IMPLEMENTATION_CONFLICT` when the requested feature can remain unchanged but the proposed task structure or
     write path conflicts with current SpecDD boundaries.
   - Use `SPEC_EVOLUTION_REQUIRED` when the requested behavior genuinely requires a durable system-contract change.
   - Use `AUTHORITY_EVOLUTION_REQUIRED` when the requested behavior genuinely requires persistent ownership or write
     permission to change.
   - Legitimate contract work may remain cross-boundary when the current authority model already permits the required
     writes and the task is not usefully decomposable.
   - A task merely touching multiple authorities is not sufficient evidence for spec or authority evolution.

10. Enforce the authority-snapshot invariant:
    - Never treat a proposed `.sdd` change as authority for the current implementation operation.
    - If `AUTHORITY_EVOLUTION_REQUIRED` applies, surface the required spec change separately.
    - After an authority-changing spec edit, end the current authority context and require a fresh
      `/speckit.specdd.context` run before implementation resumes.

## Output

Report, in task order:

- stage,
- task ID and user story when present,
- write targets,
- primary authority domains,
- deterministic task classification,
- diagnostics and severity,
- authority-local decomposition guidance when useful,
- any agentic classification that is required.

If any blocking diagnostic exists, state that implementation must not proceed under the current boundary.

Keep deterministic findings distinct from architectural interpretation.

## Constraints

- Never edit `.sdd` files.
- Never rewrite Spec Kit tasks automatically.
- Never synchronize Spec Kit task markers with SpecDD `Tasks:` entries.
- Never infer authority from task wording, directory names, or proximity.
- Never relax SpecDD ownership or write authority to make validation pass.
