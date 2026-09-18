---
description: Verify actual changes against immutable SpecDD authorization evidence.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when interpreting verification findings. User input may supply feature-specific context,
but it must not override deterministic authority or bootstrap-control results.

## Goal

Verify the resulting implementation using actual Git changes, fresh SpecDD resolution, and immutable authorization
evidence established by the successful pre-implementation gate.

The mutable feature Change Boundary is not verification authority. Current `tasks.md` is likewise not historical
authorization evidence. Authorization preserves the exact boundary plus a fingerprint-bound companion plan containing
selected `.sdd` evolution targets and explicit editable bootstrap-control selections.

This command reports state only.

## Execution

1. Locate the active feature and repository root through supported Spec Kit and Git state.

2. Require current-worktree Git metadata evidence:

       specdd/authorization-boundary.json
       specdd/authorization-spec-evolution.json

   The companion document must fingerprint-match the exact boundary snapshot.

3. Run deterministic verification:

       uv run --no-project python integration/specdd/scripts/verification.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --feature-dir "<feature-dir>" \
         --authorization-snapshot "<git-dir>/specdd/authorization-boundary.json"

4. The verifier:
   - obtains current tracked and untracked Git changes;
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
   - never expand planned `.sdd` or bootstrap-control scope from current task text;
   - never use changed `.sdd` or bootstrap-control state to justify implementation writes absent from historical
     authorization.

7. Evaluate feature/system convergence separately after deterministic verification.

## Output

Report actual implementation paths, excluded feature/generated paths, changed specifications and controls, planned
specification and bootstrap-control selections, authorized and actual authority domains, deterministic diagnostics,
`specdd lint`, and any separate convergence findings.

## Constraints

- Never edit `.sdd` files.
- Never regenerate or replace authorization evidence during verification.
- Never treat changed specification or bootstrap-control state as retroactive implementation authority.
- Never downgrade an immutable or unplanned root SpecDD control change to a warning.
- Never infer authority from Git path proximity, task wording, or directory names.
