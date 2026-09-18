---
description: Verify actual changes against immutable SpecDD authorization evidence.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when interpreting verification findings. User input may supply feature-specific context,
but it must not override deterministic authority, bootstrap-control, or operation-baseline results.

## Goal

Verify the resulting implementation using post-authorization Git changes, fresh SpecDD resolution, and immutable
authorization evidence established by the successful pre-implementation gate.

The mutable feature Change Boundary is not verification authority. Current `tasks.md` is likewise not historical
authorization evidence. Authorization preserves the exact boundary, a fingerprint-bound companion plan containing
selected `.sdd` evolution targets and explicit editable bootstrap-control selections, and a separate Git baseline.

The Git baseline records authorization-time `HEAD` plus exact content/deletion identities for every dirty path. During
verification, unchanged pre-authorization tracked modifications, staged changes, untracked files, and deletions are
excluded from the operation. If a pre-existing dirty path changes content or deletion state after authorization, it is
included. A staging-only status change with identical working-tree content remains excluded. Any new post-authorization
change, including concurrent unrelated work, remains in operation scope and is verified normally.

This command reports state only.

## Execution

1. Locate the active feature and repository root through supported Spec Kit and Git state.

2. Require current-worktree Git metadata evidence:

       specdd/authorization-boundary.json
       specdd/authorization-spec-evolution.json
       specdd/authorization-git-baseline.json

   The companion specification/control document and Git baseline must fingerprint-match the exact boundary snapshot.

3. Run deterministic verification:

       uv run --no-project python integration/specdd/scripts/verification.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --feature-dir "<feature-dir>" \
         --authorization-snapshot "<git-dir>/specdd/authorization-boundary.json"

4. The verifier:
   - obtains current tracked and untracked Git changes;
   - rejects verification when Git `HEAD` changed after authorization because the baseline is no longer safely comparable;
   - excludes dirty paths whose current content/deletion identity exactly matches the authorization-time baseline;
   - includes post-authorization changes even when they are unrelated or concurrent with the feature;
   - excludes active feature artifacts and generated Spec Kit state from implementation authority checks;
   - keeps `.specdd/bootstrap.local.md` in local/generated state;
   - reports shared root `.specdd/` control state separately;
   - compares changed `.sdd` files with exact evolution targets preserved at authorization;
   - compares changed editable bootstrap overrides with authorization-time control selections;
   - freshly resolves existing actual implementation targets;
   - checks deleted implementation targets against the historical boundary snapshot;
   - runs `specdd lint`.

5. Interpret deterministic diagnostics:
   - `AUTHORITY_VIOLATION`: actual implementation authority is unknown, conflicting, changed, or newly introduced.
   - `SPECDD_DRIFT`: an actual implementation target was not authorized even though its authority domain was.
   - `SPECDD_VIOLATION`: `specdd lint` failed.
   - `SPEC_EVOLUTION_PRESENT`: changed `.sdd` files were explicitly selected at authorization.
   - `UNPLANNED_SPEC_EVOLUTION`: changed `.sdd` files were not selected at authorization.
   - `CONTROL_STATE_CHANGED`: `.specdd/bootstrap.project.md` changed after explicit workflow or Operator selection.
   - `CONTROL_STATE_VIOLATION`: immutable `.specdd/bootstrap.md`, unrelated root SpecDD control state, or an unplanned
     project bootstrap override changed.
   - `STALE_BOUNDARY`: the authorization snapshot belongs to a different feature.

   `AUTHORITY_VIOLATION`, `SPECDD_VIOLATION`, `UNPLANNED_SPEC_EVOLUTION`, and `CONTROL_STATE_VIOLATION` are blocking.
   `CONTROL_STATE_CHANGED` is informational because authorization already recorded its explicit selection.

6. Enforce the authority-snapshot invariant:
   - never replace the snapshot with current `boundary.json`;
   - never replace or recapture the authorization-time Git baseline during verification;
   - never expand planned `.sdd` or bootstrap-control scope from current task text;
   - never use changed `.sdd` or bootstrap-control state to justify implementation writes absent from historical
     authorization.

7. Treat post-authorization concurrent work conservatively. Because Git cannot identify which process produced a new
   worktree delta, verification includes it rather than guessing. Use a dedicated worktree when concurrent feature work
   must remain isolated, but do not make worktrees part of SpecDD authority semantics.

8. Evaluate feature/system convergence separately after deterministic verification.

## Output

Report operation-scoped implementation paths, excluded pre-authorization dirty paths, excluded feature/generated paths,
changed specifications and controls, planned specification and bootstrap-control selections, authorized and actual
authority domains, deterministic diagnostics, `specdd lint`, and any separate convergence findings.

## Constraints

- Never edit `.sdd` files.
- Never regenerate or replace authorization evidence during verification.
- Never treat changed specification or bootstrap-control state as retroactive implementation authority.
- Never downgrade an immutable or unplanned root SpecDD control change to a warning.
- Never infer authority from Git path proximity, task wording, or directory names.
