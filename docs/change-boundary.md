# Change Boundary

A Change Boundary is disposable, feature-scoped integration state that projects current SpecDD ownership onto the
concrete implementation paths of one Spec Kit feature.

It answers:

> Which SpecDD authority domains own the implementation targets currently planned for this feature?

The boundary is not a specification, permission grant, task system, control-file authorization record, or historical
authorization record. Canonical system authority remains in the `.sdd` hierarchy.

## Derived feature state and operation evidence

The bridge keeps refreshable feature state separate from historical implementation evidence.

The feature Change Boundary is current planning and task context:

    specs/001-google-login/.specdd/boundary.json

Each successful boundary refresh also records a feature-keyed effective-SpecDD context document under current-worktree
Git metadata:

    <git-dir>/specdd/boundary-context/

That document is bound to the exact boundary and stores only per-target SHA-256 context identities. Each identity is
derived from the normalized resolver-returned governing spec paths and sections for that target. Rule text is not copied
into `boundary.json` or into the context document.

Successful authorization records two immutable documents in current-worktree Git metadata:

    <git-dir>/specdd/authorization-boundary.json
    <git-dir>/specdd/authorization-spec-evolution.json

The first is the exact validated Change Boundary. The second is fingerprint-bound to that snapshot and records exact
`.sdd` targets selected by explicit evolution tasks plus exact editable bootstrap overrides deliberately selected for
the operation.

Refresh-time context evidence is not authorization evidence. It may be replaced by a later context refresh. Successful
authorization first fresh-resolves the current boundary targets and verifies that their effective SpecDD context still
matches the refresh-time fingerprints. A mismatch is a blocking `STALE_BOUNDARY`.

Bootstrap-control selections also record whether selection came from an authorized workflow task or direct Operator
input. This companion document grants neither implementation authority nor new SpecDD authority.

Refreshing `boundary.json` changes neither authorization document.

## Ownership and modification permission

Change Boundary v1 records each target's primary owning specification. It deliberately does not copy `Can modify` rules
into `boundary.json`.

Task validation and authorization treat ownership and modification permission separately. An unmarked task uses its
target owners as participating operation authorities. A task declaring `SPECDD_AUTHORITY:` is fresh-resolved so every
cross-owned target must have applicable inherited `Can modify` permission.

This execution-time permission projection does not transfer ownership.

## Bootstrap control authority

Root SpecDD bootstrap controls are not Change Boundary targets.

The bridge applies the bootstrap contract separately:

- `.specdd/bootstrap.md` is immutable and cannot be selected for modification.
- `.specdd/bootstrap.project.md` may change only when explicitly selected for the operation.
- `.specdd/bootstrap.local.md` may be explicitly selected for local use, but remains generated/local state and is
  excluded from shared implementation-write verification.
- other root `.specdd/` control changes are not treated as implementation writes and are not implicitly authorized.

Workflow task text may explicitly select an editable override. Direct authorization may also record an exact editable
override explicitly named by the Operator. Authorization stores that selection before implementation begins.

Verification blocks immutable, unrelated, or unplanned shared control changes with `CONTROL_STATE_VIOLATION`.
A planned project override is reported as informational `CONTROL_STATE_CHANGED`.

## Change Boundary contents

Change Boundary v1 records:

- active feature identifier;
- resolved ordinary implementation targets;
- each target's primary SpecDD authority;
- resolved governing specs;
- distinct owning authority domains;
- whether more than one owner domain is involved;
- unresolved target diagnostics;
- SpecDD CLI and framework versions.

It deliberately does not copy persistent `Must`, `Must not`, `Owns`, `Can modify`, or dependency rules.

The separate refresh-time context document detects changes to those effective contracts without extending the v1
boundary schema or duplicating their text.

## Tracking policy

Feature Change Boundaries are generated, uncommitted state:

    specs/*/.specdd/boundary.json

Refresh-time effective-context evidence and authorization evidence are stored in Git metadata rather than the worktree.

None of these documents is a canonical source of truth. A Change Boundary and its context identities are reconstructed
from current feature paths and current SpecDD resolution. Authorization evidence is replaced only by another successful
authorization operation.

## Canonical inputs

A Change Boundary is reconstructed from concrete or intended ordinary implementation paths and current SpecDD resolver
output.

The effective-context identity uses the resolver-returned spec chain and semantic section data. This captures inherited
contract changes, explicit `References` changes, referenced contracts returned by resolution, and governing-chain
changes while ignoring unrelated worktree files.

`.sdd` evolution targets and root SpecDD bootstrap controls remain outside the Change Boundary because they do not
represent implementation ownership.

## Lifecycle

| Stage | Change Boundary and context identity | Authorization evidence |
| --- | --- | --- |
| Planning | Create or refresh from ordinary implementation targets. | Unchanged. |
| Task generation | Refresh from exact ordinary task write targets. | Unchanged. |
| Authorization | Fresh-resolve context, reject drift, preserve boundary. | Store exact boundary and companion selections. |
| Implementation | Later boundary/task changes grant no new authority. | Remains historical evidence. |
| Verification | Current boundary and context identity are not authority evidence. | Compare actual state with stored evidence. |

The installed workflow overlay applies:

    plan
      → specdd-context
      → review-plan
      → tasks
      → specdd-task-validation
      → specdd-authorize
      → implement
      → specdd-verify

## Intended non-existent targets

Pinned SpecDD CLI `1.1.1` requires `resolve` targets to exist and does not expose an intended-path authority query.

A non-existent ordinary target therefore remains `UNRESOLVED_TARGET` with an `INTENDED_TARGET_UNSUPPORTED` message.
The bridge does not inspect ownership patterns to invent pre-creation authority.

Planning may carry that uncertainty. Task validation and implementation authorization fail closed until resolver-backed
authority can be established.

## Task-stage refinement

Before task-stage validation, the structural gate regenerates the Change Boundary from exact ordinary implementation
targets and replaces the corresponding refresh-time context fingerprints.

Multi-owner work remains representable. `SPECDD_AUTHORITY:` is checked separately for non-owning modification permission.

Root `.specdd/` controls are removed from implementation target projection and remain visible to authorization as
separate control selections.

## Specification evolution

A specification change cannot grant new rights to the implementation operation already authorized.

The supported sequence is:

1. identify required specification or authority evolution;
2. apply the `.sdd` change as a separate operation;
3. end the old authority context when authority changed;
4. refresh the feature Change Boundary and effective-context identity;
5. run authorization again;
6. begin dependent implementation under new evidence.

Refreshing only `boundary.json` by hand is insufficient because authorization requires matching refresh-time context
evidence and fresh resolver output.

## Verification

Verification leaves authorization evidence unchanged.

The verifier obtains actual Git changes and separates them into feature artifacts, generated state, SpecDD
specifications, root bootstrap controls, and ordinary implementation writes.

Existing ordinary implementation targets are fresh-resolved and compared with the historical boundary. Deleted targets
must already be represented by that boundary.

Changed `.sdd` files are compared with authorization-time evolution targets.

Shared root bootstrap controls are compared with authorization-time control selections. The immutable bootstrap and
unrelated root control state always fail closed. Local bootstrap preferences remain generated/local state.

## Deterministic regeneration

Equivalent canonical inputs produce semantically equivalent feature Change Boundaries and effective-context hashes.
Generation avoids timestamps and normalizes deterministic collections.

Authorization evidence is intentionally different: it is historical state and is replaced only by successful
authorization.

## Troubleshooting

If no feature boundary is produced during planning, confirm that the plan names an exact ordinary non-spec
implementation target.

If authorization reports `STALE_BOUNDARY` after no task-path change, refresh context. A governing `.sdd` contract,
explicit reference, resolved governing chain, SpecDD CLI version, or framework version may have changed since the
boundary was generated.

If a target reports `INTENDED_TARGET_UNSUPPORTED`, either select an existing implementation target for the current
operation or defer creation until resolver-backed intended-path authority exists.

If a declared `SPECDD_AUTHORITY:` reports `AUTHORITY_VIOLATION`, inspect `modificationPermissions`; split or correct the
task rather than relaxing authority.

If verification reports `CONTROL_STATE_VIOLATION`, restore immutable/unrelated root control state or perform a new
authorization operation that explicitly selects the editable project override before changing it.
