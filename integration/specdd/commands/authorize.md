---
description: Authorize implementation against the active feature's existing SpecDD authority snapshot.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when reporting context, but user input cannot weaken deterministic authority findings.

## Goal

Run the bridge validator at implementation strictness before implementation begins. Use the existing Change Boundary as the operation's authority snapshot. Do not refresh it inside this command.

This command is the lifecycle gate used by the mandatory `before_implement` hook.

## External dependency failures

If a required external command is missing or cannot start (`pwsh` for prerequisite discovery, `git`, or `uv` when
reached), report it as an infrastructure failure and stop. Preserve the tool error, direct the user to
`bash scripts/bootstrap.sh --check`, and do not convert tool absence into stale-boundary or authority diagnostics.

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

4. Require the planned inputs:
   - If `BOUNDARY_FILE` does not exist, stop and instruct the user to run `/speckit.specdd.context`.
   - If `TASK_FILE` does not exist, stop and instruct the user to generate tasks with `/speckit.tasks`.
   - Do not regenerate `BOUNDARY_FILE` here. Authorization must evaluate the authority snapshot prepared before
     implementation.

5. Run deterministic validation at implementation strictness:

       uv run --no-project python integration/specdd/scripts/validation.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --boundary "<feature-dir>/.specdd/boundary.json" \
         --tasks "<feature-dir>/tasks.md" \
         --stage "implementation"

   Do not parse `.sdd` files or derive authority independently.

6. Inspect the validation result:
   - `AUTHORITY_VIOLATION` is blocking.
   - `STALE_BOUNDARY` at implementation strictness is blocking.
   - Invalid or unresolved task scope contributes to blocking authority validation.
   - `MULTI_AUTHORITY_TASK` alone is a warning and does not make legitimate cross-domain work invalid.
   - Evolution-scope errors are blocking when specification and implementation writes were improperly mixed.

7. If `summary.blocking` is `true`:
   - Report the blocking diagnostics and affected paths.
   - State that implementation is not authorized under the current Change Boundary.
   - Stop before any implementation task executes.
   - Do not propose relaxing current authority as the fix.

8. If `summary.blocking` is `false`:
   - Report that the current task scope is authorized for implementation under the existing boundary.
   - Include any warnings that still require implementation judgment.
   - Preserve the authority-snapshot invariant for later verification.

## Output

Keep the result compact. Report the active feature, planned authority domains, blocking status, blocking diagnostics, and
non-blocking cross-boundary warnings when present.

A successful result authorizes only the task scope represented by the current Change Boundary. It does not grant
authority to unplanned writes discovered later.

## Constraints

- Never edit `.sdd` files.
- Never edit `tasks.md`.
- Never refresh the Change Boundary inside the authorization gate.
- Never treat proposed or newly changed specification state as retroactive implementation authority.
- Never infer authority from task wording, directory names, or proximity.
