# Boundary Specification

Status: target architecture approved; native Boundary runtime active  
Project type: persistent-contract and operation-authorization infrastructure for coding agents

## Purpose

Boundary provides durable project contracts, effective target context, explicit operation scope, authorization evidence, and verification for agentic software changes.

Boundary is independent of the systems used to describe and execute an individual change.

The repository originated with Spec Kit as its change workflow, SpecDD as migration-era persistent-contract infrastructure, and Codex as its first agent runtime. The current Boundary runtime no longer uses SpecDD. Spec Kit and agent-runtime integrations remain adapters rather than product identities.

The core relationship is:

> A change system owns feature intent and execution state. Boundary owns persistent system contracts and operation authority. Agent adapters deliver relevant procedure and effective context.

## Product concepts

Boundary has the following durable concepts:

- persistent project contracts;
- explicit path ownership;
- additive scoped contract applicability;
- effective target context;
- explicit implementation write scope;
- implementation authorization;
- historical operation evidence;
- persistent-contract evolution;
- actual-write verification;
- progressive agent instruction disclosure.

These concepts must remain meaningful if the current change system or agent runtime is replaced.

## Canonical state

The target downstream canonical state consists of:

- change-system artifacts that define the requested change;
- native Boundary contracts under `contracts/`;
- one immutable Boundary source/version pin.

Generated integration state, effective-context projections, installed skills, caches, and operation evidence are not persistent system contracts.

Operation evidence is historical workflow state stored outside ordinary project source, preferably in current-worktree Git metadata.

## Native persistent contracts

Boundary defines a native contract format rather than standardizing legacy provider semantics.

Contract files:

- have explicit repository-relative scope;
- have stable contract identifiers;
- may own exact paths or subtrees;
- may apply constraints to additional explicit scopes;
- may declare architecture dependencies;
- contain concise human-readable invariants, prohibitions, and interfaces.

Contract file placement has no semantic effect.

The native model does not use `.specdd/bootstrap.md`, directory walking, nearest-file replacement, or a global catch-all project contract.

Detailed contract semantics are defined in [spec-contracts.md](spec-contracts.md).

## Additive applicability invariant

A target may be governed by several contracts.

All matching contracts apply additively.

When ownership is nested, the most specific matching owner is the target's primary owner, while broader matching owning contracts continue to contribute constraints.

A more specific contract therefore cannot silently free a target from a broader applicable contract.

Boundary v1 has no contract override or exception mechanism.

## Explicit write-scope invariant

Implementation authority must never be inferred from path-looking prose.

The change-system adapter must provide explicit write declarations for implementation tasks or their equivalent structured operation input.

Planning may heuristically inspect path mentions for advisory context. Authorization may not use those heuristics.

Every authorized implementation target must resolve to one unambiguous primary owner under the fresh native contract graph.

## Operation separation invariant

Implementation and persistent-contract evolution are different operation kinds.

An implementation operation may not modify native contract files.

A contract-evolution operation may not use its changed contracts to authorize implementation writes in the same operation.

Dependent implementation begins only after contract evolution is validated and a fresh implementation authorization succeeds.

## Authorization invariant

Authorization derives current operation scope directly from:

- canonical explicit write declarations;
- a freshly loaded native contract graph;
- current Git state.

It does not depend on a previously generated feature boundary or refresh-time fingerprint sidecar.

Successful authorization creates one atomic operation record containing all evidence required by later verification.

Mutable planning state cannot widen that record retroactively.

## Agent-context invariant

Boundary does not require a large framework bootstrap or the complete project contract set in normal agent context.

Stable procedure belongs in small reusable skills.

Operation-specific facts belong in deterministic query results.

Persistent contract prose is disclosed only when relevant to the current target or relationship.

A tiny stable set of Boundary behavioral invariants may be always available, but project-specific architecture must not be permanently injected.

## Adapter model

Boundary has two permanent integration boundaries:

- a change-system adapter;
- an agent-runtime adapter.

The current concrete integrations are Spec Kit for change-system state and Codex plus Claude Code materializers for agent procedure.

Boundary does not introduce a generalized runtime provider-plugin framework merely to abstract these implementations. Concrete adapters are preferred until actual implementations demonstrate a useful stable shared interface.

## Non-goals

Boundary does not:

- replace a product requirements or feature-specification system;
- require Spec Kit as its permanent change system;
- preserve SpecDD semantics merely for compatibility;
- require `.sdd` files or `.specdd/` state downstream;
- maintain a second compiled persistent copy of project contracts;
- authorize writes from prose path mentions;
- formalize all architectural prose into executable rules;
- make agent prompt compliance the enforcement layer;
- create a global catch-all cross-contract prompt;
- provide implicit contract override semantics;
- introduce a generalized adapter marketplace or plugin framework;
- automatically evolve persistent contracts to make implementation pass.

## Focused specifications

The design is split by responsibility:

- [spec-architecture.md](spec-architecture.md): core structures, adapters, transient projections, and deterministic boundaries.
- [spec-contracts.md](spec-contracts.md): native contract syntax and semantic model.
- [spec-agent-instructions.md](spec-agent-instructions.md): skill architecture and progressive disclosure.
- [spec-authorization.md](spec-authorization.md): explicit writes, operation records, Git baselines, epochs, and verification.
- [spec-change-adapter.md](spec-change-adapter.md): provider-neutral change-system projection and Spec Kit integration.
- [spec-lifecycle.md](spec-lifecycle.md): integration with change systems, contract evolution, implementation, and convergence.
- [change-boundary.md](change-boundary.md): legacy documentation retained temporarily for migration history.

Historical v0.1 acceptance material describes how the original bridge established its baseline; it is not the current product architecture.

## Migration status

Native Boundary semantics have replaced the migration-era provider path.

The supported runtime no longer depends on:

- persisted feature Change Boundaries;
- refresh-time context fingerprint sidecars;
- a separate public validation lifecycle stage;
- `SPECDD_AUTHORITY:` operation identity;
- mixed implementation/specification authorization;
- three-file authorization evidence;
- SpecDD bootstrap injection;
- duplicated extension-hook and workflow-overlay enforcement.

Remaining cleanup is documentation, historical-material, compatibility-test, and release-packaging work rather than runtime semantic migration.

## Summary invariant

Boundary remains coherent while:

> project contracts are canonical and independently scoped; change systems provide explicit change intent; skills provide procedure; queries provide current facts; and deterministic code provides authorization and verification.
