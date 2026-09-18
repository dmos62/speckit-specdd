# Change Boundary

A Change Boundary is disposable, feature-scoped integration state that projects current SpecDD authority onto the
concrete implementation paths of one Spec Kit feature.

It answers:

> Which SpecDD authority domains govern the implementation targets currently planned for this feature?

The boundary is not a specification, permission grant, task system, or historical authorization record. Canonical
system authority remains in the `.sdd` hierarchy.

For the broader responsibility split and normal workflow, see [../README.md](../README.md). For installation and
development-host procedures, see [development.md](development.md).

## Two derived states

The bridge keeps two deliberately different derived states.

The feature Change Boundary is refreshable planning and task context:

    specs/001-google-login/.specdd/boundary.json

The implementation authorization snapshot is the exact validated boundary accepted immediately before implementation.
It lives outside the worktree in the current worktree's Git metadata:

    <git-dir>/specdd/authorization-boundary.json

The authorization snapshot is replaced only by a later successful authorization. Refreshing `boundary.json` does not
change it.

This separation preserves historical authority evidence if a specification or Change Boundary changes during or after
the implementation operation.

## Change Boundary contents

Change Boundary v1 records:

- the active feature identifier;
- resolved non-spec implementation targets;
- each target's primary SpecDD authority;
- the resolved governing specs for each target;
- the distinct authority domains involved;
- whether more than one authority domain is involved;
- unresolved target diagnostics;
- SpecDD CLI and framework versions used for generation.

It deliberately does not copy persistent `Must`, `Must not`, `Owns`, `Can modify`, or dependency rules from `.sdd`
files.

The authorization snapshot uses the same validated Change Boundary document. It is a historical copy, not another
schema or authority model.

## Tracking policy

Feature Change Boundaries are generated, uncommitted state. The repository ignore policy covers:

    specs/*/.specdd/boundary.json

The authorization snapshot is stored in Git metadata rather than the worktree, so it cannot become a committed project
artifact accidentally.

Neither file is a canonical source of truth. A Change Boundary is reconstructed from current feature paths and current
SpecDD resolution. An authorization snapshot is reconstructed only by performing a new successful authorization
operation.

## Canonical inputs

A Change Boundary is reconstructed from:

- concrete or intended paths named by Spec Kit feature artifacts or supplied explicitly;
- the current SpecDD hierarchy;
- fresh output from the installed SpecDD resolver for targets the resolver can inspect.

The bridge delegates SpecDD resolution to the real `specdd` CLI. It does not parse `.sdd` source as an independent
authority engine.

## Lifecycle

| Stage | Change Boundary | Authorization snapshot |
| --- | --- | --- |
| Planning | Create or refresh from exact plan targets when available. | Unchanged. |
| Task generation | Refresh from exact non-spec task write targets. | Unchanged. |
| Authorization | Preserve and validate the existing boundary. | On success, copy the exact validated boundary into Git metadata. |
| Implementation | May not gain authority from later boundary or spec changes. | Remains immutable for this operation. |
| Verification | Current boundary is not authority evidence. | Compare actual writes against this snapshot plus fresh target resolution. |

The installed workflow overlay applies these stages as:

    plan
      → specdd-context
      → review-plan
      → tasks
      → specdd-task-validation
      → specdd-authorize
      → implement
      → specdd-verify

## Planning target discovery

During structural workflow execution, the planning context gate reads exact repository paths from `plan.md`.

Only concrete repository paths are candidates. The bridge does not derive implementation targets from code symbols,
URLs, library names, headings, similar filenames, or architectural guesses.

`.sdd` paths are excluded because specification evolution is not implementation authority.

If planning contains no concrete non-spec target, the structural context gate removes any previous feature boundary
rather than presenting stale current context.

When `/speckit.specdd.context` is invoked directly, explicit target paths supplied by the user take precedence.
Otherwise the command prefers exact paths from `tasks.md`, then exact paths from `plan.md`.

## Intended non-existent targets

SpecDD permits an intended ordinary-file path only when its pre-operation authority is established by the applicable
`Owns` or `Can modify` contract. The bridge must not turn that rule into a local approximation.

Pinned SpecDD CLI `1.1.1` requires `resolve` targets to exist and does not expose a separate intended-path authority
query. For a non-existent target, Change Boundary generation therefore keeps the normalized path in `unresolved` with
code `UNRESOLVED_TARGET` and an `INTENDED_TARGET_UNSUPPORTED` message. The bridge does not inspect ownership patterns to
invent a pre-creation authority result.

This state means creation authority is unsupported by the current bridge/tool combination, not that SpecDD forbids the
file. It is advisory during planning. Task-stage validation fails on it, and implementation authorization also fails
until resolver-backed authority can be established.

## Task-stage refinement

Task generation is where implementation scope must become precise.

Before task-stage validation, the structural gate regenerates the Change Boundary from exact non-`.sdd` task targets.
A multi-domain feature may therefore contain several authorities.

A task target absent from this refreshed boundary is not silently accepted as an implied write.

## Unresolved targets

The boundary can retain an input as unresolved instead of inventing authority.

| Code | Meaning |
| --- | --- |
| `INVALID_TARGET` | The input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | The path is valid input but one primary authority cannot currently be established. For non-existent paths, `INTENDED_TARGET_UNSUPPORTED` in the message identifies the pinned resolver limitation. |
| `RESOLUTION_FAILED` | The SpecDD resolver failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | More than one resolved specification claims ownership. |

Unresolved scope is advisory during planning but becomes an error during task validation. Unknown or conflicting
implementation authority blocks authorization.

Unresolved context never grants permission.

## Stale boundaries

A feature Change Boundary is stale when it no longer represents the active feature or task write scope.

`STALE_BOUNDARY` is reported when, for example:

- the boundary feature identifier differs from the active feature;
- a current task write target is absent from the boundary projection.

At task stage stale scope is an error. At authorization it blocks creation of a new authorization snapshot.

A stale or refreshed feature boundary does not mutate an already established authorization snapshot.

## Authorization snapshot

Successful authorization performs two operations in order:

1. validate the existing feature boundary against current tasks at implementation strictness;
2. atomically copy that exact validated boundary to the worktree Git metadata.

Validation failure leaves any prior snapshot unchanged.

The snapshot represents the authority context for the implementation operation that follows. Verification must use it
even if `boundary.json` is refreshed later.

A later successful authorization replaces the snapshot and therefore begins a new implementation authority context.

## Specification evolution

A specification change cannot grant new rights to the implementation operation already authorized.

The supported sequence is:

1. identify required specification or authority evolution;
2. apply the `.sdd` change as a separate operation;
3. end the old authority context when authority itself changed;
4. refresh the feature Change Boundary;
5. run authorization again;
6. begin dependent implementation under the newly recorded snapshot.

Refreshing only `boundary.json` is insufficient. The previous authorization snapshot remains the historical authority
evidence until a new authorization succeeds.

## Verification

Verification keeps the authorization snapshot unchanged.

The verifier obtains actual implementation writes from Git and separates them from active feature artifacts, generated
Spec Kit state, changed `.sdd` files, and root SpecDD bootstrap control state.

Existing actual implementation targets are freshly resolved through SpecDD and compared with the snapshot.

This distinguishes:

- an actual target retaining its authorized authority;
- an unplanned target inside an already authorized authority domain;
- an actual write introducing an authority domain absent from the snapshot;
- a target whose authority changed after authorization;
- changed specifications that cannot retroactively justify implementation.

Deleted implementation targets cannot be freshly resolved, so their authority must already be represented by the
snapshot.

## Deterministic regeneration

Equivalent canonical inputs produce semantically equivalent feature Change Boundaries. Generation avoids timestamps and
normalizes deterministic collections.

The authorization snapshot is intentionally different: it is not refreshed by context generation. A new copy is
created only by successful authorization.

## Troubleshooting

If no feature boundary is produced during planning, confirm that the plan names an exact non-spec repository target.

If a non-existent target reports `INTENDED_TARGET_UNSUPPORTED`, either select an existing implementation target for the
current operation or defer file creation until the SpecDD toolchain can provide resolver-backed intended-path
authority. Do not infer ownership from nearby `.sdd` files to bypass the diagnostic.

If another target is unresolved, verify the intended path and its SpecDD ownership chain. Do not infer authority from
directory proximity.

If `AMBIGUOUS_AUTHORITY` appears, correct the competing ownership claims.

If task validation reports `STALE_BOUNDARY`, refresh context before authorization.

If authorization fails, no new snapshot is created.

If verification reports a missing authorization snapshot, run the normal authorization gate before implementation.
Do not regenerate a boundary and treat that as historical authorization evidence.
