# Integration Lifecycle Semantics

This document defines how SpecDD context participates in the Spec Kit feature lifecycle. Structural data and adapter architecture are documented in [spec-architecture.md](spec-architecture.md).

## Normal lifecycle

The bridge lifecycle is:

    context → validate → authorize → implement → verify

The installed workflow overlay positions these operations around the upstream Spec Kit steps so objective authority checks do not depend only on an agent remembering to invoke them.

## Context

`speckit.specdd.context` builds or refreshes the current feature Change Boundary from concrete or intended ordinary implementation targets.

It calls the existing bridge adapter and real SpecDD resolver. It does not parse `.sdd` source independently, infer authority from naming or proximity, or treat specification evolution as implementation permission.

Each successful refresh also records fingerprint-bound effective SpecDD context identities in current-worktree Git metadata.

These fingerprints are disposable freshness evidence, not authorization evidence.

Planning may continue with unresolved targets, but unresolved context never grants permission.

## Validation

`speckit.specdd.validate` checks Spec Kit task write targets against the current Change Boundary.

Validation preserves primary ownership and separately projects non-owning modification permission when a task explicitly declares `SPECDD_AUTHORITY:`.

Lifecycle strictness increases from `planning` to `tasks` to `implementation`.

The validator surfaces deterministic findings such as:

- unresolved target scope;
- stale boundary scope;
- multi-authority tasks;
- invalid declared operation authority;
- missing `Can modify` permission;
- malformed or mixed specification-evolution scope.

Architectural reasoning then distinguishes implementation conflict from genuine contract or authority evolution.

Validation does not create historical implementation authorization.

## Authorization

`speckit.specdd.authorize` is the blocking pre-implementation gate.

It requires the existing Change Boundary, task list, and matching refresh-time context evidence. It does not regenerate the boundary.

Authorization fresh-resolves each resolved boundary target and compares the effective SpecDD context with the refresh-time fingerprints. A changed governing contract, reference, governing chain, owner, or resolver generation identity produces blocking `STALE_BOUNDARY`.

Successful authorization stores three documents in current-worktree Git metadata:

    specdd/authorization-boundary.json
    specdd/authorization-spec-evolution.json
    specdd/authorization-git-baseline.json

The boundary snapshot is the exact validated ownership projection.

The companion plan records exact `.sdd` evolution targets and explicitly selected editable bootstrap controls. It grants no implementation authority.

The Git baseline records authorization-time `HEAD` and exact content or deletion identities for every dirty path.

Failed authorization does not replace prior successful evidence.

## Verification

`speckit.specdd.verify` compares post-authorization Git state with immutable historical evidence.

The current feature boundary and current tasks are not verification authority.

Verification:

- excludes unchanged dirty state that already existed at authorization;
- includes a pre-existing dirty path when its content or deletion state changed afterward;
- includes clean paths that became dirty after authorization;
- fails closed when Git `HEAD` changed;
- excludes generated integration state and active feature artifacts from implementation authority checks;
- validates changed `.sdd` files against authorization-time evolution selections;
- validates root bootstrap-control changes against authorization-time selections;
- freshly resolves existing actual implementation targets;
- checks deleted implementation targets against the historical boundary;
- runs `specdd lint`.

Concurrent post-authorization work remains part of the operation because Git cannot identify which process produced a worktree delta. An optional dedicated worktree can isolate concurrent operations.

## Specification evolution

A feature may legitimately require a durable SpecDD contract change.

Such work uses explicit `SPEC_EVOLUTION_REQUIRED:` task text and names only `.sdd` targets.

The specification change occurs separately from dependent ordinary implementation. After evolution, context is refreshed and dependent implementation receives fresh authorization.

The changed specification never retroactively authorizes writes already performed in the previous operation.

## Authority evolution

Ownership and modification-permission changes use explicit `AUTHORITY_EVOLUTION_REQUIRED:` task text.

Authority evolution ends the prior authority context.

Any implementation that depends on the new owner or permission state begins only after:

1. the `.sdd` authority change is applied;
2. the feature boundary and effective context are refreshed;
3. authorization succeeds again;
4. a new Git baseline is captured.

## Promotion into SpecDD

Not every feature requirement should become persistent system specification.

A useful promotion question is:

> If this information were forgotten after the feature shipped, could a future developer make a locally reasonable but systemically invalid change?

Durable architectural invariants, ownership rules, security invariants, cross-component contracts, dependency restrictions, and persistent local behavior are candidates for SpecDD.

One-time migration sequencing, rollout tasks, temporary feature mechanics, and historical discussion normally remain in Spec Kit feature history.

Promotion is deliberate. The bridge does not automatically edit `.sdd` files.

## Constitution versus root SpecDD

The Spec Kit constitution and root SpecDD specification are separate policy layers.

The constitution governs development process, for example test requirements, compatibility review, migration process, or security review.

Root SpecDD governs persistent system architecture, for example dependency direction, persistence isolation, or cross-service contracts.

Equivalent-looking rules should live at the layer matching their semantic purpose rather than being copied into both.

## Convergence

Combined convergence has three dimensions:

- feature correctness: implementation satisfies Spec Kit feature intent;
- system correctness: resulting state satisfies SpecDD contracts;
- governance correctness: work satisfies the Spec Kit constitution.

Authority verification remains distinct from convergence.

Authority verification asks whether the operation was permitted under historical system boundaries. Convergence asks whether the resulting implementation satisfies feature, system, and governance intent.

Relevant SpecDD convergence diagnostics include:

- `SPECDD_VIOLATION`;
- `SPECDD_DRIFT`;
- `AUTHORITY_VIOLATION`;
- `UNPLANNED_SPEC_EVOLUTION`;
- `CONTROL_STATE_VIOLATION`;
- agentic `MISSING_SPEC_EVOLUTION`.

Blocking authority, control-state, or SpecDD lint findings prevent a clean converged result.
