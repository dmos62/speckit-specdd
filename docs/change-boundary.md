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

Each successful boundary refresh also records feature-keyed effective-SpecDD context under current-worktree Git
metadata:

    <git-dir>/specdd/boundary-context/

That document is bound to the exact boundary and stores only per-target SHA-256 context identities derived from the
normalized resolver-returned governing spec paths and sections. Rule text is not copied into `boundary.json` or context
metadata.

Successful authorization records three operation-evidence documents:

    <git-dir>/specdd/authorization-boundary.json
    <git-dir>/specdd/authorization-spec-evolution.json
    <git-dir>/specdd/authorization-git-baseline.json

The first is the exact validated Change Boundary. The second is fingerprint-bound to that snapshot and records exact
`.sdd` targets selected by explicit evolution tasks plus exact editable bootstrap overrides deliberately selected for
the operation. The third is also fingerprint-bound and records authorization-time Git `HEAD` plus content/deletion
identities for every dirty path.

Refresh-time context evidence is not authorization evidence and may be replaced by a later context refresh. Successful
authorization first fresh-resolves current boundary targets and verifies that their effective SpecDD context still
matches the refresh-time fingerprints. A mismatch is blocking `STALE_BOUNDARY`.

Bootstrap-control selections record whether selection came from an authorized workflow task or direct Operator input.
The companion documents grant neither implementation authority nor new SpecDD authority. Refreshing `boundary.json`
changes none of the authorization documents.

## Operation-scoped Git baseline

Verification compares the final dirty worktree with the baseline captured after authorization validation succeeds and
before new operation evidence is written.

Every path already dirty at authorization is recorded regardless of whether it is an unstaged tracked modification, a
staged change, an untracked file, or a deletion. If that path has the same content/deletion identity at verification, it
is excluded as pre-authorization state. If its content or deletion state changed after authorization, it participates in
verification like any other operation write. A staging-only transition with unchanged working-tree content does not
become an implementation write.

A clean path that becomes dirty after authorization is always part of the operation. This includes concurrent unrelated
work: Git cannot safely identify which process produced a post-authorization delta, so the bridge does not guess.
Dedicated feature worktrees are optional isolation when concurrent changes must not share verification scope.

The baseline also records Git `HEAD`. If `HEAD` changes before verification, comparison fails closed and fresh
authorization is required. This keeps the baseline an operation boundary without turning Change Boundary v1 into an
operation log.

## Ownership and modification permission

Change Boundary v1 records each target's primary owning specification. It deliberately does not copy `Can modify` rules
into `boundary.json`.

Task validation and authorization treat ownership and modification permission separately. An unmarked task uses its
target owners as participating operation authorities. A task declaring `SPECDD_AUTHORITY:` is fresh-resolved so every
cross-owned target must have applicable inherited `Can modify` permission. This execution-time permission projection
does not transfer ownership.

## Bootstrap control authority

Root SpecDD bootstrap controls are not Change Boundary targets.

- `.specdd/bootstrap.md` is immutable and cannot be selected for modification.
- `.specdd/bootstrap.project.md` may change only when explicitly selected for the operation.
- `.specdd/bootstrap.local.md` may be selected for local use but remains generated/local state and is excluded from
  shared implementation-write verification.
- Other root `.specdd/` control changes are not implementation writes and are not implicitly authorized.

Workflow task text may select an editable override. Direct authorization may also record an exact editable override
explicitly named by the Operator. Verification blocks immutable, unrelated, or unplanned shared control changes with
`CONTROL_STATE_VIOLATION`; a planned project override is informational `CONTROL_STATE_CHANGED`.

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

It deliberately does not copy persistent `Must`, `Must not`, `Owns`, `Can modify`, or dependency rules. The separate
refresh-time context document detects changes to effective contracts without extending the v1 schema or duplicating
rule text.

## Semantic consistency

JSON Schema shape validation is not sufficient before a Change Boundary can influence authorization or verification.
Boundary readers also validate deterministic relationships between fields.

Resolved target paths must be unique. `authorities` must equal the distinct non-null `primaryAuthority` values projected
by those targets, and `crossBoundary` must agree with that authority set. When a target has a non-null primary authority,
that authority must appear in the target's `resolvedSpecs`.

A normalized path cannot appear both as a resolved and unresolved target. `candidateAuthorities` is reserved for
`AMBIGUOUS_AUTHORITY`, where at least two candidates must be present.

Change Boundary v1 retains nullable `primaryAuthority` as a conservative compatibility state. Current generation does
not intentionally emit a resolved target with null authority; inability to derive one primary owner normally appears in
`unresolved`. A shape-valid v1 document containing null authority is treated as unknown authority and never grants
implementation permission.

## Tracking policy and canonical inputs

Feature Change Boundaries are generated, uncommitted state:

    specs/*/.specdd/boundary.json

Refresh-time context evidence and all authorization evidence live in Git metadata rather than the worktree. None of
these documents is a canonical source of truth.

A Change Boundary is reconstructed from concrete or intended ordinary implementation paths and current SpecDD resolver
output. Effective-context identity uses the resolver-returned spec chain and semantic section data, capturing inherited
contract changes, explicit `References`, referenced contracts, and governing-chain changes while ignoring unrelated
worktree files.

`.sdd` evolution targets and root SpecDD bootstrap controls remain outside the Change Boundary because they do not
represent implementation ownership.

## Lifecycle

| Stage | Change Boundary and context identity | Authorization evidence |
| --- | --- | --- |
| Planning | Create or refresh from ordinary implementation targets. | Unchanged. |
| Task generation | Refresh from exact ordinary task write targets. | Unchanged. |
| Authorization | Fresh-resolve context and reject drift. | Store exact boundary, companion selections, and Git baseline. |
| Implementation | Later boundary/task changes grant no new authority. | Baseline remains the operation start state. |
| Verification | Current boundary and context identity are not authority evidence. | Compare only post-baseline Git state with historical authority evidence. |

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

Pinned SpecDD CLI `1.1.1` requires `resolve` targets to exist and exposes no intended-path authority query.

A non-existent ordinary target therefore remains `UNRESOLVED_TARGET` with an `INTENDED_TARGET_UNSUPPORTED` message.
The bridge does not inspect ownership patterns to invent pre-creation authority. Planning may carry that uncertainty;
task validation and authorization fail closed until resolver-backed authority can be established.

## Task-stage refinement

Before task-stage validation, the structural gate regenerates the Change Boundary from exact ordinary implementation
targets and replaces corresponding refresh-time context fingerprints.

Multi-owner work remains representable. `SPECDD_AUTHORITY:` is checked separately for non-owning modification
permission. Root `.specdd/` controls are removed from implementation projection and remain separate control selections.

## Specification evolution

A specification change cannot grant new rights to the implementation operation already authorized.

The supported sequence is:

1. identify required specification or authority evolution;
2. apply the `.sdd` change as a separate operation;
3. end the old authority context when authority changed;
4. refresh the feature Change Boundary and effective-context identity;
5. run authorization again, which also captures a new Git baseline;
6. begin dependent implementation under the new evidence.

Refreshing only `boundary.json` by hand is insufficient because authorization requires matching refresh-time context
evidence and fresh resolver output.

## Verification

Verification leaves authorization evidence unchanged. It first filters current Git state against the authorization-time
baseline, then separates remaining changes into feature artifacts, generated state, SpecDD specifications, root
bootstrap controls, and ordinary implementation writes.

Existing ordinary implementation targets are fresh-resolved and compared with the historical boundary. Deleted targets
must already be represented by that boundary. Changed `.sdd` files are compared with authorization-time evolution
targets. Shared root bootstrap controls are compared with authorization-time control selections. The immutable bootstrap
and unrelated root control state fail closed; local bootstrap preferences remain generated/local state.

## Deterministic regeneration

Equivalent canonical inputs produce semantically equivalent feature Change Boundaries and effective-context hashes.
Generation avoids timestamps and normalizes deterministic collections. Authorization evidence is intentionally
historical state and is replaced only by successful authorization.

## Troubleshooting

If no feature boundary is produced during planning, confirm that the plan names an exact ordinary non-spec target.

If authorization reports `STALE_BOUNDARY` after no task-path change, refresh context. A governing `.sdd` contract,
explicit reference, resolved governing chain, SpecDD CLI version, or framework version may have changed.

If verification reports that Git `HEAD` changed after authorization, run a fresh authorization from the current
repository state. Use an optional dedicated worktree when independent concurrent work must continue without entering the
same operation scope.

If a target reports `INTENDED_TARGET_UNSUPPORTED`, either select an existing implementation target for the current
operation or defer creation until resolver-backed intended-path authority exists.

If a declared `SPECDD_AUTHORITY:` reports `AUTHORITY_VIOLATION`, inspect `modificationPermissions`; split or correct the
task rather than relaxing authority.

If verification reports `CONTROL_STATE_VIOLATION`, restore immutable/unrelated root control state or perform a new
authorization operation that explicitly selects the editable project override before changing it.
