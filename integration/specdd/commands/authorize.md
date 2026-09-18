---
description: Authorize implementation and preserve immutable SpecDD operation evidence.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input when reporting context, but user input cannot weaken deterministic authority findings.
An exact editable bootstrap override named directly by the Operator may be passed to the structural gate with
`--operator-control`. Never translate a general request into such a selection by inference.

## Goal

Validate the active feature at implementation strictness before implementation begins. The current Change Boundary is the
candidate ownership projection. Successful authorization copies that exact validated boundary into immutable operation
evidence stored in worktree Git metadata.

Authorization also records a fingerprint-bound companion plan. It contains exact `.sdd` targets selected by explicit
`SPEC_EVOLUTION_REQUIRED:` or `AUTHORITY_EVOLUTION_REQUIRED:` tasks plus explicitly selected editable bootstrap
overrides. Bootstrap-control selections record whether they came from an authorized workflow task or direct Operator
selection. None of this companion state grants implementation authority.

The immutable `.specdd/bootstrap.md` can never be selected. The only editable root bootstrap overrides are
`.specdd/bootstrap.project.md` and `.specdd/bootstrap.local.md`; the latter remains local/generated state and is excluded
from shared implementation-write verification.

Ownership and modification permission remain distinct. Unmarked tasks execute under their target owner domains. When
task text declares one operation authority with `SPECDD_AUTHORITY:`, authorization fresh-resolves that authority context
and verifies `Can modify` permission for cross-owned writes.

## Execution

1. Locate the active feature with the supported Spec Kit prerequisite command and resolve the Git repository root.

2. Require:
   - `FEATURE_DIR/.specdd/boundary.json`;
   - `FEATURE_DIR/tasks.md`.

   Do not regenerate the Change Boundary here.

3. Run the structural authorization gate:

       uv run --no-project python integration/specdd/scripts/workflow_gate.py authorize \
         --root "<repository-root>"

   For each exact editable bootstrap override explicitly named by the Operator in this command invocation, append:

       --operator-control ".specdd/bootstrap.project.md"

   or:

       --operator-control ".specdd/bootstrap.local.md"

   Do not pass `.specdd/bootstrap.md` or infer control selection from intent that does not name the exact path.

4. The gate:
   - validates the existing Change Boundary against `tasks.md` at `implementation` strictness;
   - fresh-resolves declared task authority context where `Can modify` permission must be distinguished from ownership;
   - treats root `.specdd/` control paths in tasks as control selections rather than implementation boundary targets;
   - rejects immutable or unrelated root SpecDD control selections;
   - records workflow-task control selections as `workflow` and direct command selections as `operator`;
   - extracts exact `.sdd` targets only from explicit evolution tasks;
   - does not replace prior authorization evidence when validation fails;
   - on success writes the validated boundary and fingerprint-bound companion plan under current-worktree Git metadata.

5. Blocking conditions include:
   - `AUTHORITY_VIOLATION`;
   - stale or unresolved implementation scope;
   - malformed or mixed evolution scope;
   - `CONTROL_STATE_VIOLATION` for `.specdd/bootstrap.md` or unrelated root control state.

6. On success report:
   - planned owner domains;
   - declared and resulting operation authorities;
   - exact planned `.sdd` evolution targets;
   - selected bootstrap overrides and whether each was selected by `workflow` or `operator`;
   - authorization evidence status;
   - non-blocking cross-authority warnings.

## Authority Snapshot Invariant

Later Change Boundary refreshes, task edits, specification changes, or bootstrap-control changes do not alter the
authorization evidence for the current operation.

Specification or authority evolution that dependent implementation must rely on requires a separate specification
operation, fresh context, and fresh authorization.

## Constraints

- Never edit `.sdd` files.
- Never edit `tasks.md`.
- Never refresh the Change Boundary inside authorization.
- Never select `.specdd/bootstrap.md` for modification.
- Never infer bootstrap-control selection from proximity or descriptive intent.
- Never treat proposed or newly changed specification or control state as retroactive implementation authority.
- Never relax ownership or modification authority to make implementation pass.
