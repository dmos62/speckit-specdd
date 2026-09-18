# Change Boundary

A Change Boundary is disposable, feature-scoped integration state that projects current SpecDD ownership onto the
concrete implementation paths of one Spec Kit feature.

It answers:

> Which SpecDD authority domains own the implementation targets currently planned for this feature?

The boundary is not a specification, permission grant, task system, or historical authorization record. Canonical
system authority remains in the `.sdd` hierarchy.

For the broader responsibility split and normal workflow, see [../README.md](../README.md). For installation and
development-host procedures, see [development.md](development.md).

## Derived feature state and operation evidence

The bridge keeps refreshable feature state separate from historical implementation evidence.

The feature Change Boundary is current planning and task context:

    specs/001-google-login/.specdd/boundary.json

Successful authorization records two documents in the current worktree's Git metadata:

    <git-dir>/specdd/authorization-boundary.json
    <git-dir>/specdd/authorization-spec-evolution.json

The first is the exact validated Change Boundary. The second contains only exact `.sdd` targets selected by explicit
`SPEC_EVOLUTION_REQUIRED:` or `AUTHORITY_EVOLUTION_REQUIRED:` tasks. It is fingerprint-bound to the boundary snapshot so
a partially replaced or mismatched evidence pair fails closed.

The specification-evolution plan is not part of Change Boundary v1, is not a permission grant, and does not copy SpecDD
contract text. It records deliberate task selection so verification can distinguish planned specification edits from
unplanned ones without rereading mutable `tasks.md` as historical evidence.

Refreshing `boundary.json` changes neither authorization document.

## Ownership and modification permission

Change Boundary v1 records each target's primary owning specification. It deliberately does not copy `Can modify` rules
into `boundary.json`.

Task validation and authorization treat ownership and modification permission separately. An unmarked task uses its
target owners as the participating operation authorities; a multi-owner task therefore remains representable and is
reported structurally rather than rejected merely for spanning domains.

When task text declares one operation authority with the literal `SPECDD_AUTHORITY:` followed by a backticked
repository-relative `.sdd` path, the bridge fresh-resolves that authority context through the real `specdd` CLI. Each
target keeps its `primaryAuthority`. Any target owned by another spec must be covered by an inherited `Can modify` grant
in the declared authority context, or task-stage validation errors and implementation authorization blocks.

The validation result exposes `operationAuthorities` and `modificationPermissions` so the owning spec remains visible
beside any non-owning grant source. This permission projection is execution-time derived context; it is not another
persistent authority store.

## Change Boundary contents

Change Boundary v1 records:

- the active feature identifier;
- resolved non-spec implementation targets;
- each target's primary SpecDD authority;
- the resolved governing specs for each target;
- the distinct owning authority domains involved;
- whether more than one owning authority domain is involved;
- unresolved target diagnostics;
- SpecDD CLI and framework versions used for generation.

It deliberately does not copy persistent `Must`, `Must not`, `Owns`, `Can modify`, or dependency rules from `.sdd`
files.

The authorization boundary snapshot uses the same validated Change Boundary document. Successful authorization is the
evidence that task scope, including any required declared-authority modification-permission check, passed before that
snapshot was stored.

## Tracking policy

Feature Change Boundaries are generated, uncommitted state. The repository ignore policy covers:

    specs/*/.specdd/boundary.json

Authorization evidence is stored in Git metadata rather than the worktree, so it cannot become a committed project
artifact accidentally.

None of these documents is a canonical source of truth. A Change Boundary is reconstructed from current feature paths
and current SpecDD resolution. Authorization evidence is replaced only by another successful authorization operation.

## Canonical inputs

A Change Boundary is reconstructed from:

- concrete or intended paths named by Spec Kit feature artifacts or supplied explicitly;
- the current SpecDD hierarchy;
- fresh output from the installed SpecDD resolver for targets the resolver can inspect.

The authorization-time specification-evolution plan is reconstructed from exact `.sdd` targets named by explicit
evolution tasks after implementation-stage validation succeeds.

The bridge delegates SpecDD resolution to the real `specdd` CLI. It does not parse `.sdd` source as an independent
authority engine.

## Lifecycle

| Stage | Change Boundary | Authorization evidence |
| --- | --- | --- |
| Planning | Create or refresh from exact plan targets when available. | Unchanged. |
| Task generation | Refresh from exact non-spec task write targets. | Unchanged. |
| Authorization | Preserve boundary; validate ownership and declared cross-owned permission. | Store exact boundary and explicit `.sdd` evolution targets. |
| Implementation | Later boundary/task changes grant no new authority. | Remains historical evidence for this operation. |
| Verification | Current boundary is not authority evidence. | Compare actual writes with the stored boundary and planned `.sdd` target list. |

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

When `/speckit.specdd.context` is invoked directly, explicit target paths supplied by the user take precedence. Otherwise
the command prefers exact paths from `tasks.md`, then exact paths from `plan.md`.

## Intended non-existent targets

SpecDD permits an intended ordinary-file path only when its pre-operation authority is established by applicable `Owns`
or `Can modify` contract. The bridge must not turn that rule into a local approximation.

Pinned SpecDD CLI `1.1.1` requires `resolve` targets to exist and does not expose a separate intended-path authority
query. For a non-existent target, Change Boundary generation therefore keeps the normalized path in `unresolved` with
code `UNRESOLVED_TARGET` and an `INTENDED_TARGET_UNSUPPORTED` message. The bridge does not inspect ownership patterns to
invent a pre-creation authority result.

This state means creation authority is unsupported by the current bridge/tool combination, not that SpecDD forbids the
file. It is advisory during planning. Task-stage validation fails on it, and implementation authorization also fails
until resolver-backed authority can be established.

## Task-stage refinement

Task generation is where implementation scope must become precise.

Before task-stage validation, the structural gate regenerates the Change Boundary from exact non-`.sdd` task targets. A
multi-domain feature may therefore contain several owners.

Validation preserves those owners. Unmarked multi-owner tasks remain coordinated across their owner domains. A task that
declares one `SPECDD_AUTHORITY:` is checked separately for `Can modify` permission on every cross-owned target. A task
target absent from the refreshed boundary is not silently accepted as an implied write.

Explicit evolution tasks keep their `.sdd` targets outside the Change Boundary. Those exact paths are preserved only
when authorization succeeds, for later verification of deliberate specification edits.

## Unresolved targets and stale boundaries

The boundary can retain an input as unresolved instead of inventing authority.

| Code | Meaning |
| --- | --- |
| `INVALID_TARGET` | The input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | The path is valid input but one primary authority cannot currently be established. |
| `RESOLUTION_FAILED` | The SpecDD resolver failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | More than one resolved specification claims ownership. |

Unresolved scope is advisory during planning but becomes an error during task validation. Unknown, conflicting, or
unpermitted implementation authority blocks authorization. Unresolved context never grants permission.

A feature Change Boundary is stale when it no longer represents the active feature or task write scope. At task stage
stale scope is an error. At authorization it blocks replacement of operation evidence. A stale or refreshed feature
boundary does not mutate evidence from a previous successful authorization.

## Specification evolution

A specification change cannot grant new rights to the implementation operation already authorized.

The supported sequence is:

1. identify required specification or authority evolution;
2. apply the `.sdd` change as a separate operation;
3. end the old authority context when authority itself changed;
4. refresh the feature Change Boundary;
5. run authorization again;
6. begin dependent implementation under the new authorization evidence.

Refreshing only `boundary.json` is insufficient. Current operation evidence remains historical until a new authorization
succeeds.

## Verification

Verification leaves authorization evidence unchanged.

The verifier obtains actual Git changes and separates them from active feature artifacts, generated Spec Kit state,
changed `.sdd` files, and root SpecDD bootstrap control state.

Existing actual implementation targets are freshly resolved through SpecDD and compared with the boundary snapshot.
Deleted implementation targets cannot be freshly resolved, so their authority must already be represented by that
snapshot.

Changed `.sdd` files are compared with the authorization-time specification-evolution target list. Planned changes are
reported as `SPEC_EVOLUTION_PRESENT` and still grant no implementation authority. Added, modified, or deleted `.sdd`
files absent from that list produce blocking `UNPLANNED_SPEC_EVOLUTION`.

## Deterministic regeneration

Equivalent canonical inputs produce semantically equivalent feature Change Boundaries. Generation avoids timestamps and
normalizes deterministic collections.

Authorization evidence is intentionally different: it is not refreshed by context generation. A new pair is recorded
only by successful authorization.

## Troubleshooting

If no feature boundary is produced during planning, confirm that the plan names an exact non-spec repository target.

If a non-existent target reports `INTENDED_TARGET_UNSUPPORTED`, either select an existing implementation target for the
current operation or defer file creation until the SpecDD toolchain can provide resolver-backed intended-path authority.
Do not infer ownership from nearby `.sdd` files to bypass the diagnostic.

If another target is unresolved, verify the intended path and its SpecDD ownership chain. If a task with a declared
`SPECDD_AUTHORITY:` reports `AUTHORITY_VIOLATION`, inspect `modificationPermissions`; remove the declaration for genuinely
coordinated owner-local work, split the task, or correct the implementation path rather than relaxing authority.

If verification reports missing or mismatched authorization evidence, run the normal authorization gate before
implementation. Do not regenerate a boundary or reread current tasks and treat them as historical authorization.
