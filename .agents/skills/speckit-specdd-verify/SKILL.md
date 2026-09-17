---
name: speckit-specdd-verify
description: Verify actual implementation changes against the planned SpecDD authority snapshot.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: SpecDD contributors
  source: specdd:commands/verify.md
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when interpreting verification findings. User input may supply feature-specific context,
but it must not override deterministic authority results.

## Goal

Verify the resulting implementation using actual Git changes, fresh SpecDD resolution, and the operation's existing
Change Boundary. Keep authority verification distinct from feature convergence and from architectural judgment about
durable specification evolution.

This command reports state only. It does not edit implementation files, Spec Kit artifacts, or `.sdd` files.

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

4. Require the planned authority snapshot:
   - If `BOUNDARY_FILE` does not exist, stop and instruct the user to run `/speckit.specdd.context`.
   - Do not regenerate the planned boundary before verification. It represents the authority context under which the
     implementation operation was expected to run.

5. Run deterministic actual-change verification:

       uv run --no-project python integration/specdd/scripts/verification.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --feature-dir "<feature-dir>" \
         --boundary "<feature-dir>/.specdd/boundary.json"

   The verifier:
   - gets current tracked and untracked changes from Git,
   - excludes active feature artifacts and generated Spec Kit integration state from implementation authority checks,
   - reports changed `.sdd` and SpecDD bootstrap control files separately,
   - freshly resolves every existing actual non-spec implementation target,
   - compares actual target authority with the planned Change Boundary,
   - checks deleted targets against the planned authority snapshot because they no longer exist for fresh resolution,
   - runs `specdd lint`.

6. Interpret deterministic diagnostics:
   - `AUTHORITY_VIOLATION`: actual authority is unknown, conflicting, changed from the snapshot, or introduces an
     authority domain absent from the planned Change Boundary. This is blocking.
   - `SPECDD_DRIFT`: an actual write was not planned even though its freshly resolved authority was already in the
     planned authority set. Treat this as system-scope drift requiring review.
   - `SPECDD_VIOLATION`: `specdd lint` failed for the resulting repository state. This is blocking.
   - `SPEC_EVOLUTION_PRESENT`: `.sdd` files changed. This is informational and never grants authority to the current
     operation.
   - `CONTROL_STATE_CHANGED`: root SpecDD bootstrap control state changed and requires explicit review.
   - `STALE_BOUNDARY`: the planned boundary belongs to a different feature. This is blocking.

7. Enforce the authority-snapshot invariant:
   - Never use a changed `.sdd` file to justify an implementation write that was not authorized by the planned
     boundary.
   - If fresh resolution reflects new authority introduced by the same operation, keep the authority finding blocking.
   - Authority-changing specification work must finish as a separate operation, followed by a fresh
     `/speckit.specdd.context` before implementation begins under the new authority.

8. Evaluate convergence separately after deterministic verification:
   - Use `FEATURE_GAP` or `CONTRADICTS_FEATURE` only for mismatches with Spec Kit feature intent.
   - Use `MISSING_SPEC_EVOLUTION` when the resulting implementation introduces a durable system contract that future
     work must preserve but no corresponding deliberate SpecDD evolution exists.
   - Do not infer `MISSING_SPEC_EVOLUTION` merely because a file was unplanned or a task crossed authorities.
   - Use `SPECDD_DRIFT` for mismatch between resulting implementation scope and current persistent system intent.
   - Keep feature findings, system findings, and authority findings visibly distinct.

9. If any blocking deterministic diagnostic exists, state that the implementation cannot be accepted under the current
   authority snapshot. Do not propose relaxing current authority as the fix.

## Output

Report:

- actual implementation write paths,
- excluded feature/generated paths,
- changed SpecDD specifications and bootstrap controls,
- planned and actual authority domains,
- deterministic diagnostics,
- `specdd lint` result,
- feature convergence findings when applicable,
- likely missing durable spec evolution when architectural reasoning supports it.

Keep deterministic authority facts distinct from agentic convergence interpretation.

## Constraints

- Never edit `.sdd` files.
- Never regenerate the planned boundary before comparing actual writes with it.
- Never treat `.sdd` changes in the current operation as new implementation authority.
- Never infer authority from Git path proximity, task wording, or directory names.
- Never duplicate persistent SpecDD constraints into verification output.