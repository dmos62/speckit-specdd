---
description: Authorize implementation and preserve immutable SpecDD operation evidence.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when reporting context, but user input cannot weaken deterministic authority findings.

## Goal

Validate the active feature at implementation strictness before implementation begins. The current Change Boundary is the
candidate ownership projection. Successful authorization copies that exact validated boundary into immutable operation
evidence stored in worktree Git metadata.

Authorization also records a companion specification-evolution plan containing only exact `.sdd` targets selected by
explicit `SPEC_EVOLUTION_REQUIRED:` or `AUTHORITY_EVOLUTION_REQUIRED:` tasks. This companion record is not part of the
Change Boundary and grants no implementation authority. Verification uses it only to distinguish deliberately selected
specification edits from unplanned `.sdd` changes.

Ownership and modification permission are distinct. Unmarked tasks execute under their target owner domains. When task
text declares one operation authority with the literal `SPECDD_AUTHORITY:` followed by a backticked repository-relative
`.sdd` path, authorization uses fresh SpecDD resolver output to verify that authority owns or has inherited `Can modify`
permission for every non-`.sdd` write target. A non-owning grant never replaces the target's `primaryAuthority`.

Later Change Boundary refreshes do not modify the authorization evidence. Only a later successful authorization starts a
new implementation operation by replacing it.

This command is the lifecycle gate used by the mandatory `before_implement` hook.

## External dependency failures

If a required external command is missing or cannot start (`pwsh` for prerequisite discovery, `git`, `uv`, or `specdd`
when reached), report it as an infrastructure failure and stop. Preserve the tool error, direct the user to
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
   - fresh-resolves declared task authority context when `Can modify` permission must be distinguished from ownership;
   - fails on deterministic `error` or `blocking` diagnostics;
   - extracts exact `.sdd` targets only from explicit evolution tasks after validation succeeds;
   - does not replace prior authorization evidence when validation fails;
   - after successful validation, atomically writes each evidence document to current-worktree Git metadata under
     `specdd/authorization-boundary.json` and `specdd/authorization-spec-evolution.json`.

5. Interpret the validation result:
   - `AUTHORITY_VIOLATION` is blocking, including a declared task authority that does not own or have `Can modify`
     permission for every write target.
   - `STALE_BOUNDARY` at implementation strictness is blocking.
   - Invalid or unresolved task scope contributes to blocking authority validation.
   - `MULTI_AUTHORITY_TASK` remains a structural warning for unmarked coordinated work across owner domains and for
     declared-authority tasks whose write set still has several owners.
   - `modificationPermissions` keeps each target owner separate from non-owning `Can modify` grant sources.
   - Evolution-scope errors are blocking when specification and implementation writes were improperly mixed.

6. If `summary.blocking` is `true` or the gate returns nonzero:
   - report the blocking diagnostics and affected paths;
   - state that implementation is not authorized under the current Change Boundary;
   - stop before any implementation task executes;
   - do not propose relaxing current authority as the fix.

7. On success:
   - report the planned owner domains;
   - report declared task authority and resulting `operationAuthorities` when present;
   - report the exact planned specification-evolution targets;
   - report that both authorization evidence documents were stored;
   - include any non-blocking cross-authority warnings;
   - treat that evidence, not subsequent `boundary.json` or `tasks.md` contents, as the historical context for this
     implementation operation.

## Authority Snapshot Invariant

A later `/speckit.specdd.context` refresh may update the feature Change Boundary for a future operation, but it does not
change current authorization evidence. Editing `tasks.md` later also cannot retroactively change which `.sdd` edits were
selected for the operation.

Specification or authority evolution that dependent implementation must rely on therefore requires:

1. completing the specification operation;
2. refreshing the Change Boundary;
3. running authorization again to establish new operation evidence;
4. only then beginning dependent implementation.

## Output

Keep the result compact. Report the active feature, planned owner domains, planned `.sdd` evolution targets, declared and
resulting operation authorities when present, blocking status, authorization evidence status, blocking diagnostics, and
non-blocking cross-boundary warnings.

## Constraints

- Never edit `.sdd` files.
- Never edit `tasks.md`.
- Never refresh the Change Boundary inside authorization.
- Never treat proposed or newly changed specification state as retroactive implementation authority.
- Never infer non-owning modification permission from task wording, directory names, or proximity.
