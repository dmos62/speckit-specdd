# Change Boundary

A Change Boundary is disposable, feature-scoped integration state that projects SpecDD authority onto the concrete implementation paths of one Spec Kit feature.

It answers a narrow question:

> Which SpecDD authority domains govern the implementation targets currently planned for this feature?

The boundary is not a specification, permission grant, task system, or copy of persistent SpecDD constraints. Canonical system authority remains in the `.sdd` hierarchy.

For the broader responsibility split and normal workflow, see [../README.md](../README.md). For installation, rematerialization, and development-host procedures, see [development.md](development.md).

## Stored state

For a feature such as:

    specs/001-google-login/

the derived boundary is stored at:

    specs/001-google-login/.specdd/boundary.json

Change Boundary v1 records:

- the active feature identifier,
- resolved non-spec implementation targets,
- each target's primary SpecDD authority,
- the resolved governing specs for each target,
- the distinct authority domains involved,
- whether more than one authority domain is involved,
- unresolved target diagnostics,
- SpecDD CLI and framework versions used for generation.

It deliberately does not copy persistent `Must`, `Must not`, `Owns`, `Can modify`, or dependency rules from `.sdd` files.

## Tracking policy

Feature Change Boundaries are generated, uncommitted state by default.

The repository ignore policy covers:

    specs/*/.specdd/boundary.json

No feature boundary is a canonical review artifact or persistent source of truth. A clean clone is expected to reconstruct the boundary from current Spec Kit feature artifacts and the current SpecDD hierarchy rather than receive a committed copy.

If a future workflow deliberately requires committed boundary evidence, treat that as an explicit repository-policy change and review the lifecycle and source-of-truth implications before changing the ignore policy.

## Canonical inputs

A boundary is reconstructed from canonical project state:

- concrete or intended paths named by Spec Kit feature artifacts or supplied explicitly,
- the current SpecDD hierarchy,
- fresh output from the installed SpecDD resolver.

The bridge delegates SpecDD resolution to the real `specdd` CLI. It does not parse `.sdd` source as an independent authority engine.

Because the boundary is derived from those inputs, it is safe to delete and rebuild.

## Lifecycle

The correct treatment of the boundary changes as the feature lifecycle becomes more precise.

| Stage | Boundary behavior | Authority meaning |
| --- | --- | --- |
| Planning | Create or refresh from exact plan targets when available. | Advisory projection; unresolved early scope may remain. |
| Task generation | Refresh from exact non-spec task write targets. | Task scope must become structurally trustworthy before implementation. |
| Authorization | Preserve the existing boundary without refreshing it. | The existing file is the operation's authority snapshot. |
| Implementation | Do not expand authority by changing the boundary or specifications. | Writes remain limited by the authorized snapshot. |
| Verification | Preserve the planned boundary and freshly resolve actual existing Git write targets for comparison. | New, changed, unknown, or conflicting authority cannot be justified retroactively. |

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

Only concrete repository paths are candidates. The bridge does not derive implementation targets from:

- code symbols,
- URLs,
- library names,
- headings,
- similar filenames,
- architectural guesses.

`.sdd` paths are excluded from the Change Boundary because specification evolution is not implementation authority.

If planning contains no concrete non-spec target yet, the structural context gate removes any previous boundary rather than presenting stale derived state as current authority. Planning may continue without a boundary until implementation paths become concrete.

When `/speckit.specdd.context` is invoked directly, explicit target paths supplied by the user take precedence. Without explicit targets, the command prefers exact paths from `tasks.md`, then exact paths from `plan.md`.

## Task-stage refinement

Task generation is the point where implementation scope is expected to become precise.

Before task-stage validation, the structural gate regenerates the boundary from the exact non-`.sdd` write targets in `tasks.md`.

This refresh is intentional: the task list is normally more precise than the earlier plan.

A multi-domain feature may therefore produce a boundary containing several authorities. That is not automatically invalid. The validator can report authority groups so naturally separable work can remain authority-local while the feature and user-story structure remain intact.

A task target absent from the freshly prepared boundary is not silently accepted as an implied write.

## Unresolved targets

A boundary can retain an input as unresolved instead of inventing authority for it.

The current diagnostic classes are:

| Code | Meaning |
| --- | --- |
| `INVALID_TARGET` | The input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | The path is valid input but one primary authority cannot currently be established. |
| `RESOLUTION_FAILED` | The SpecDD resolver failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | More than one resolved specification claims ownership. |

A missing intended file can therefore remain visible as `UNRESOLVED_TARGET` instead of disappearing from the projection.

Unresolved scope has lifecycle-dependent consequences:

- during planning it is advisory because exact implementation structure may still be emerging;
- during task validation it is an error that must be corrected before implementation scope is considered complete;
- during implementation authorization, unknown or conflicting authority contributes to blocking `AUTHORITY_VIOLATION`.

Unresolved context never grants permission.

## Stale boundaries

A boundary is stale when it no longer represents the active feature or the implementation scope being validated.

Deterministic validation reports `STALE_BOUNDARY` when, for example:

- the boundary feature identifier differs from the active feature;
- a current task write target is absent from the boundary projection.

At task stage, stale scope is an error. At implementation stage, stale scope blocks authorization.

The normal correction is to refresh the boundary before implementation, not to weaken validation.

Refresh is expected:

- after planning identifies concrete implementation paths;
- after task generation finalizes exact non-spec write targets;
- after a separate deliberate SpecDD evolution operation, before dependent implementation begins.

Refresh is forbidden inside the authorization or verification gates because those stages need the existing boundary as historical evidence of the authority context under which implementation was expected to run.

## Authority snapshot

After task scope has been refreshed and validated, the existing boundary becomes the implementation operation's authority snapshot.

`specdd-authorize` evaluates that snapshot without regenerating it.

This distinction is necessary because a feature may require deliberate `.sdd` evolution. A specification change cannot grant new rights to the same implementation operation that performs the change.

The supported sequence is:

1. identify required specification or authority evolution;
2. apply the `.sdd` change as a separate operation;
3. end the prior authority context when authority itself changed;
4. refresh the Change Boundary;
5. begin dependent implementation under the newly resolved authority.

A changed `.sdd` file never retroactively authorizes an implementation write made under an older boundary.

## Verification

Verification keeps the planned boundary unchanged.

The verifier obtains actual implementation writes from Git and separates them from:

- active feature artifacts,
- generated Spec Kit integration state,
- changed `.sdd` specifications,
- root SpecDD bootstrap control state.

Existing actual implementation targets are freshly resolved through SpecDD and compared with the planned snapshot.

This allows verification to distinguish cases such as:

- an actual target retaining its planned authority;
- an unplanned target inside an already planned authority domain;
- an actual write introducing an authority domain absent from the snapshot;
- a target whose authority changed after planning;
- a changed `.sdd` file appearing in the same operation.

Deleted implementation targets cannot be freshly resolved, so their permission must already be represented by the planned boundary.

## Deterministic regeneration

Equivalent canonical inputs produce semantically equivalent boundary state.

Generation intentionally avoids timestamps. The output records stable tool-version metadata and normalizes deterministic collections so the file can be rebuilt and compared in tests.

To rebuild the active feature through the normal command flow, use:

    /speckit.specdd.context

The structural workflow performs the corresponding refresh automatically at the planning and task gates.

Deleting `boundary.json` does not delete system intent. It only removes a cached projection. The next valid refresh reconstructs it from feature paths and current SpecDD resolver output.

## Troubleshooting

If no boundary is produced during planning, confirm that the plan names at least one exact non-spec repository target. Absence of a concrete early target is allowed and should not leave an older boundary in place.

If a target is unresolved, verify the intended path and its SpecDD ownership chain. Do not infer authority from directory proximity.

If `AMBIGUOUS_AUTHORITY` appears, correct the competing ownership claims. The bridge must not choose one owner by proximity.

If task validation reports `STALE_BOUNDARY`, refresh context from the finalized task paths before authorization.

If authorization reports unknown or conflicting authority, implementation must remain blocked until trustworthy authority exists.

If specification or authority evolution was just completed, generate a fresh boundary before any implementation relies on the changed contract.

Installation and generated-state repair procedures remain in [development.md](development.md); this guide only describes Change Boundary semantics and lifecycle behavior.
