# Boundary Architecture

This document defines Boundary's target structural architecture. Contract semantics, agent instruction delivery, authorization evidence, and lifecycle transitions are documented separately.

## Architectural boundaries

Boundary has four target layers.

### Boundary core

The core owns provider-independent mechanics:

- repository path normalization;
- explicit operation write scope;
- contract-graph queries;
- target ownership projection;
- effective-context composition;
- operation authorization;
- Git operation baselines;
- actual-write verification;
- provider-neutral diagnostics;
- atomic operation evidence.

The core does not know about Spec Kit command names, Codex skill directories, SpecDD sections, `.sdd`, or `.specdd/`.

### Native contract engine

The native contract engine:

- discovers `contracts/**/*.contract.md`;
- parses contract frontmatter and semantic sections;
- validates path scopes and ownership relationships;
- constructs the in-memory `ContractGraph`;
- resolves `TargetContext`;
- exposes relevant interface context for declared dependencies;
- validates contract-only evolution results.

The graph is rebuilt from canonical contracts. It is not a persistent second source of truth.

### Change-system adapter

A change-system adapter translates an external change workflow into Boundary inputs.

Its responsibilities are limited to concepts such as:

- active change identifier;
- canonical task identity;
- explicit declared write targets;
- adapter-owned feature artifacts;
- lifecycle integration points.

The initial adapter is Spec Kit.

Boundary's core semantics must not require Spec Kit-specific stages, files, command syntax, or constitution concepts.

### Agent-runtime adapter

An agent-runtime adapter materializes Boundary's canonical skills and thin entry points for an agent environment.

The initial adapter is Codex.

Canonical skill content uses Boundary concepts rather than vendor-specific tool syntax. Agent-specific wrappers may map those concepts onto local commands.

## Transitional SpecDD compatibility adapter

During migration, the repository may retain a concrete SpecDD compatibility adapter.

Its only purpose is to keep current behavior available while native contracts and tests are introduced.

Any remaining SpecDD-specific behavior belongs behind this boundary, including:

- `specdd resolve`;
- `.sdd` parsing or resolver-output interpretation;
- `Owns` and `Can modify`;
- SpecDD framework bootstrap state;
- intended-target capability probing;
- `specdd lint`;
- SpecDD CLI/framework identity.

The compatibility adapter is temporary and is removed after repository contracts and downstream tests use native Boundary semantics.

It must not define the core API.

## Core data model

The target core operates on a small set of provider-independent structures.

### Contract

A parsed canonical persistent contract containing:

- stable ID;
- source path;
- owned scopes;
- additional applicable scopes;
- declared dependencies;
- semantic sections;
- content identity.

### ContractGraph

An in-memory validated graph containing:

- contracts by ID;
- ownership scope index;
- applicability scope index;
- dependency edges.

The graph is transient and deterministic for equivalent canonical contract contents.

### TargetContext

A derived projection for one repository target:

- target path;
- primary owner;
- applicable contract IDs;
- effective invariants and prohibitions;
- relevant dependency interfaces;
- source provenance.

Target context is query output, not canonical state.

### ChangeContext

Input supplied by a change-system adapter:

- change identifier;
- operation kind;
- task identity where applicable;
- exact declared write targets;
- adapter-owned non-implementation artifacts.

The core never discovers authorization scope from arbitrary prose.

### OperationRecord

Historical evidence for one authorized operation:

- operation identifier;
- change identifier;
- operation kind;
- exact authorized targets;
- target ownership/effective-context identities;
- Git `HEAD`;
- dirty-path baseline;
- predecessor/carry-forward evidence when applicable;
- lifecycle status.

One operation is represented by one atomic document.

## Source layout direction

The canonical implementation should migrate toward a provider-neutral layout similar to:

    src/boundary/
      contracts/
      context/
      authorization/
      verification/
      cli/

    skills/
      scope/
      implement/
      contracts/

    adapters/
      speckit/
      codex/
      specdd-compat/

    schemas/

The exact packaging may change while migration is underway, but provider names must not define core package boundaries.

Installed/generated integration state remains separate from this canonical source.

## Deterministic versus agentic responsibility

Deterministic code owns facts that can be computed reliably:

- valid path syntax;
- contract parsing;
- scope containment;
- ownership selection;
- applicability;
- explicit write-set equality;
- Git baseline comparison;
- undeclared-write detection;
- operation-kind separation;
- contract graph structural validity.

Agentic reasoning owns semantics that cannot be mechanically established from the contract structure alone:

- whether a feature requirement implies a durable new invariant;
- how an invariant should be phrased;
- whether implementation satisfies prose intent;
- whether a dependency or interface should be redesigned;
- whether a cross-component task should be decomposed for maintainability.

The architecture should move a concern into deterministic code only when doing so does not create an unreliable second interpretation of prose semantics.

## No persisted planning boundary

Boundary does not require a feature-local `boundary.json`.

Planning and task generation may call `boundary inspect` and receive target projections, but those projections are disposable query results.

Authorization always resolves canonical task scope against a fresh `ContractGraph`.

This removes:

- boundary refresh lifecycle state;
- refresh-time fingerprint sidecars;
- stale feature-boundary synchronization;
- a provider-named feature-state namespace.

## No generalized provider framework

Boundary should use concrete internal interfaces only where they simplify current code.

Do not add:

- dynamic provider registration;
- provider manifests;
- configurable semantic engines;
- runtime adapter discovery.

The native contract engine is the product implementation.

SpecDD is a migration adapter, not the first member of a permanent provider ecosystem.

A generalized abstraction is justified only after another real implementation demonstrates shared requirements.

## Portability invariant

Replacing Spec Kit, Codex, or the SpecDD compatibility layer must not require redesigning:

- native contract semantics;
- target effective-context composition;
- explicit write authorization;
- operation evidence;
- Git verification;
- contract-evolution separation.

Those are Boundary concepts.
