---
description: Authorize implementation and preserve an immutable SpecDD authority snapshot.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when reporting context, but user input cannot weaken deterministic authority findings.

## Goal

Validate the active feature at implementation strictness before implementation begins. The current Change Boundary is the
candidate authority projection. Successful authorization copies that exact validated boundary into an immutable
operation snapshot stored in worktree Git metadata.

Later Change Boundary refreshes do not modify the authorization snapshot. Only a later successful authorization starts a
new implementation operation by replacing the snapshot.

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

3. Require:
   - `FEATURE_DIR/.specdd/boundary.json`;
   - `FEATURE_DIR/tasks.md`.

   Do not regenerate the Change Boundary here.

4. Run the canonical structural authorization gate:

       uv run --no-project python integration/specdd/scripts/workflow_gate.py authorize \
         --root "<repository-root>"

   The gate:
   - validates the existing Change Boundary against `tasks.md` at the `implementation` lifecycle stage;
   - fails on deterministic `error` or `blocking` diagnostics;
   - does not replace a prior authorization snapshot when validation fails;
   - after successful validation, atomically copies the validated Change Boundary to the current worktree Git metadata
     under `specdd/authorization-boundary.json`.

5. Interpret the validation result:
   - `AUTHORITY_VIOLATION` is blocking.
   - `STALE_BOUNDARY` at implementation strictness is blocking.
   - Invalid or unresolved task scope contributes to blocking authority validation.
   - `MULTI_AUTHORITY_TASK` alone is a warning and does not make legitimate cross-domain work invalid.
   - Evolution-scope errors are blocking when specification and implementation writes were improperly mixed.

6. If `summary.blocking` is `true` or the gate returns nonzero:
   - report the blocking diagnostics and affected paths;
   - state that implementation is not authorized under the current Change Boundary;
   - stop before any implementation task executes;
   - do not propose relaxing current authority as the fix.

7. On success:
   - report the planned authority domains;
   - report that the immutable authorization snapshot was stored;
   - include any non-blocking cross-authority warnings;
   - treat that snapshot, not subsequent `boundary.json` contents, as the authority evidence for this implementation
     operation.

## Authority Snapshot Invariant

A later `/speckit.specdd.context` refresh may update the feature Change Boundary for a future operation, but it does not
change the current authorization snapshot.

Specification or authority evolution that dependent implementation must rely on therefore requires:

1. completing the specification operation;
2. refreshing the Change Boundary;
3. running authorization again to establish a new operation snapshot;
4. only then beginning dependent implementation.

## Output

Keep the result compact. Report the active feature, planned authority domains, blocking status, authorization snapshot
status, blocking diagnostics, and non-blocking cross-boundary warnings when present.

## Constraints

- Never edit `.sdd` files.
- Never edit `tasks.md`.
- Never refresh the Change Boundary inside authorization.
- Never treat proposed or newly changed specification state as retroactive implementation authority.
- Never infer authority from task wording, directory names, or proximity.
