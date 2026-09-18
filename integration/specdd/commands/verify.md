---
description: Verify actual implementation changes against the immutable SpecDD authorization snapshot.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when interpreting verification findings. User input may supply feature-specific context,
but it must not override deterministic authority results.

## Goal

Verify the resulting implementation using actual Git changes, fresh SpecDD resolution, and the immutable authorization
snapshot established by the successful pre-implementation gate.

The mutable feature Change Boundary is not verification authority. It may have been refreshed after authorization and
must not replace the historical snapshot for the current implementation operation.

This command reports state only. It does not edit implementation files, Spec Kit artifacts, or `.sdd` files.

## External dependency failures

If a required external command is missing or cannot start (`pwsh` for prerequisite discovery, `git`, `uv`, or `specdd`
when reached), report it as an infrastructure failure and stop. Preserve the tool error, direct the user to
`bash scripts/bootstrap.sh --check`, and do not convert tool absence into lint, drift, stale-boundary, or authority
diagnostics.

## Execution

1. From the repository root, run:

       .specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly

   Parse `FEATURE_DIR` from the JSON result. If the command fails or no active feature is available, stop and instruct
   the user to create or select a feature with `/speckit.specify`.

2. Resolve the repository root with:

       git rev-parse --show-toplevel

   Treat that path as the bridge root. `FEATURE_DIR` must resolve inside it. Stop if the active feature is outside the
   repository root.

3. Derive `FEATURE_ID` as the basename of `FEATURE_DIR`.

4. Resolve the authorization snapshot from the current worktree Git metadata:

       git rev-parse --git-dir

   The bridge stores the snapshot below that directory at:

       specdd/authorization-boundary.json

   If the snapshot does not exist, stop. Implementation verification requires a successful authorization operation.

5. Run deterministic actual-change verification:

       uv run --no-project python integration/specdd/scripts/verification.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --feature-dir "<feature-dir>" \
         --authorization-snapshot "<git-dir>/specdd/authorization-boundary.json"

   The verifier:
   - gets current tracked and untracked changes from Git;
   - excludes active feature artifacts and generated Spec Kit integration state from implementation authority checks;
   - reports changed `.sdd` and SpecDD bootstrap control files separately;
   - freshly resolves every existing actual non-spec implementation target;
   - compares actual target authority with the immutable authorization snapshot;
   - checks deleted targets against the snapshot because they no longer exist for fresh resolution;
   - runs `specdd lint`.

6. Interpret deterministic diagnostics:
   - `AUTHORITY_VIOLATION`: actual authority is unknown, conflicting, changed from the snapshot, or introduces an
     authority domain absent from the snapshot. This is blocking.
   - `SPECDD_DRIFT`: an actual write was not authorized as a target even though its freshly resolved authority was
     already in the authorized authority set. Treat this as system-scope drift requiring review.
   - `SPECDD_VIOLATION`: `specdd lint` failed for the resulting repository state. This is blocking.
   - `SPEC_EVOLUTION_PRESENT`: `.sdd` files changed. This is informational and never grants authority to the current
     operation.
   - `CONTROL_STATE_CHANGED`: root SpecDD bootstrap control state changed and requires explicit review.
   - `STALE_BOUNDARY`: the authorization snapshot belongs to a different feature. This is blocking.

7. Enforce the authority-snapshot invariant:
   - never use the current feature `boundary.json` to replace the authorization snapshot during verification;
   - never use a changed `.sdd` file to justify an implementation write absent from the snapshot;
   - if fresh resolution reflects authority introduced after authorization, keep the authority finding blocking;
   - authority-changing specification work must finish separately, followed by fresh context and fresh authorization.

8. Evaluate convergence separately after deterministic verification:
   - use `FEATURE_GAP` or `CONTRADICTS_FEATURE` only for mismatches with Spec Kit feature intent;
   - use `MISSING_SPEC_EVOLUTION` when implementation introduces a durable system contract future work must preserve but
     corresponding deliberate SpecDD evolution is absent;
   - do not infer `MISSING_SPEC_EVOLUTION` merely because a file was unplanned or a task crossed authorities;
   - keep feature findings, system findings, and authority findings visibly distinct.

9. If any blocking deterministic diagnostic exists, state that the implementation cannot be accepted under the
   authorization snapshot. Do not propose relaxing current authority as the fix.

## Output

Report actual implementation write paths, excluded feature/generated paths, changed specifications and controls,
authorized and actual authority domains, deterministic diagnostics, the `specdd lint` result, and any separate
convergence findings.

## Constraints

- Never edit `.sdd` files.
- Never regenerate or replace the authorization snapshot during verification.
- Never treat `.sdd` changes in the current operation as new implementation authority.
- Never infer authority from Git path proximity, task wording, or directory names.
- Never duplicate persistent SpecDD constraints into verification output.
