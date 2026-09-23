# Boundary Lifecycle Semantics

Boundary integrates with a change process without making that process part of its product identity.

The current change-system adapter is Spec Kit. Another change system, or a future Boundary-native change workflow, must be able to drive the same Boundary lifecycle.

## Mandatory implementation lifecycle

Boundary's mandatory lifecycle is:

    authorize → implement → verify

Planning and task generation may use Boundary context, but they do not establish implementation authority.

This is deliberately smaller than the currently implemented:

    context → validate → authorize → implement → verify

The current `context` and `validate` behavior becomes query/analysis functionality reused by planning, task generation, and authorization.

## Planning

During planning an agent may:

- inspect candidate target contracts;
- identify ownership;
- discover applicable invariants and interfaces;
- classify likely contract evolution;
- refine implementation paths.

Planning context is advisory.

Heuristic path discovery is acceptable here because planning output cannot grant write permission.

No feature-local authorization artifact is created.

## Task generation

Before tasks are considered implementation-ready, the change-system adapter supplies explicit write declarations.

The Boundary scope skill helps the agent:

- name exact intended writes;
- inspect their effective context;
- separate contract evolution from implementation;
- prefer coherent owner-local tasks where useful.

A user story may span any number of owner domains.

A coordinated task may also span several owners.

Boundary v1 does not require a synthetic task authority identity.

## Authorization

Authorization is the blocking transition into implementation.

It uses:

- canonical explicit writes;
- fresh native contracts;
- current Git state.

It does not refresh an earlier boundary and does not prove an earlier planning cache fresh.

Successful authorization creates the historical operation record consumed by verification.

An existing unverified operation cannot be silently replaced by another authorization epoch.

## Implementation

Implementation runs under one active implementation operation.

The implementation skill instructs the agent to:

- inspect relevant effective contract context;
- modify only authorized targets;
- stop before scope expansion;
- transition out of implementation when persistent contracts need evolution.

Deterministic checks remain authoritative even if an agent fails to follow the skill.

A Git `HEAD` transition during an active operation invalidates the baseline and prevents successful verification.

## Scope expansion

When implementation discovers another required target:

1. the target may be inspected;
2. it may not be written under the current operation;
3. the current operation is verified and closed;
4. a new operation is authorized;
5. verified predecessor state may be carried forward only when its exact Git state is unchanged.

A verified predecessor is archived only when the successor actually relies on that carry-forward evidence.

Scope expansion does not require discarding valid completed work, but it does require an explicit authorization epoch transition.

## Verification

Verification compares actual Git changes with the historical operation record.

It does not use:

- current task prose;
- current planning projections;
- a regenerated feature boundary.

Verification reports authorization correctness only.

Successful verification closes the current authorization epoch by marking its operation record verified and recording final dirty-state identities for authorized targets. Those identities provide the only provenance accepted for dirty-target carry-forward into a later epoch.

Feature correctness and broader convergence are separate.

## Contract evolution

When requested behavior cannot satisfy current persistent contracts:

1. stop dependent implementation;
2. verify and close the current implementation operation, or abandon it through an explicit future lifecycle mechanism;
3. begin a `contract-evolution` operation;
4. use the Boundary contracts skill;
5. modify only native contract files;
6. run `boundary contracts check`;
7. verify/close contract evolution;
8. authorize dependent implementation against the resulting fresh graph.

Contract evolution never retroactively authorizes earlier implementation.

## Convergence

Boundary distinguishes:

- operation correctness: actual writes matched historical authorization;
- contract structural correctness: the native contract graph is valid;
- feature correctness: implementation satisfies requested behavior;
- semantic system correctness: implementation respects applicable prose contracts;
- development governance: the active change system's process rules are satisfied.

Only the first two are fully deterministic Boundary-core concerns in v1.

The current Spec Kit constitution is one change-system governance implementation, not a Boundary architectural layer.

## Product CLI direction

The canonical product-level command surface should converge toward:

    boundary inspect <target...>
    boundary contracts check
    boundary authorize
    boundary verify

Additional status/debugging commands may be introduced when justified.

These commands use Boundary terminology and do not depend on a particular change system.

## Spec Kit adapter

The initial Spec Kit adapter may expose thin agent-facing wrappers such as:

    speckit.boundary.authorize
    speckit.boundary.verify

Those names belong to the adapter.

They are not the canonical Boundary product API.

The Spec Kit workflow integration should eventually enforce only:

    tasks
      → boundary-authorize
      → implement
      → boundary-verify

Planning/task augmentations may invoke Boundary skills and inspection, but they should not create redundant structural gates.

## Extension hooks and workflow overlays

The current implementation registers both extension hooks and structural workflow-overlay steps for overlapping lifecycle responsibilities.

The target architecture uses one mechanism for deterministic structural enforcement.

For the current Spec Kit baseline, the workflow overlay is preferred because its ordering and nonzero shell status are explicit.

Extension hooks should not duplicate authorization or verification gates.

## Preset role

The current large SpecDD preset should not survive mechanically.

If Spec Kit still needs an augmentation after native skills exist, it should be minimal, for example:

- instruct task generation to load `boundary-scope`;
- require explicit `Writes:` metadata;
- instruct implementation to load `boundary-implement`.

If those responsibilities can be supplied through supported skill discovery without a preset, the preset should be removed.

## Adapter replacement

Replacing Spec Kit must require only a new change-system adapter that can provide:

- active change identity;
- explicit operation writes;
- lifecycle calls around implementation;
- classification of its own generated/change artifacts.

Native contracts, skills, authorization semantics, and Git verification remain unchanged.
