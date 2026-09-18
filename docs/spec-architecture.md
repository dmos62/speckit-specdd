# Integration Architecture

This document defines the structural bridge between Spec Kit feature work and persistent SpecDD authority. Lifecycle sequencing and evolution procedures are documented separately in [spec-lifecycle.md](spec-lifecycle.md).

## Change Boundary

The central integration abstraction is the Change Boundary.

A Change Boundary is a derived projection of the persistent SpecDD model onto one Spec Kit feature. It answers which SpecDD authority domains own the ordinary implementation targets currently associated with that feature.

For a feature such as `specs/001-google-login/`, derived state lives at:

    specs/001-google-login/.specdd/boundary.json

The boundary is disposable cache/integration state. It is not a specification, permission grant, task system, or historical authorization record.

### Boundary contents

Change Boundary v1 records:

- schema version;
- feature identifier;
- resolved ordinary implementation targets;
- primary SpecDD authority per resolved target;
- governing specifications returned by resolution;
- distinct authority domains;
- whether multiple domains are involved;
- unresolved target diagnostics;
- deterministic tool-generation metadata.

It does not copy persistent `Must`, `Must not`, `Owns`, `Can modify`, dependency, or other durable SpecDD rule text.

Refresh-time effective-context fingerprints are stored separately in current-worktree Git metadata and remain bound to the exact generated boundary.

### Semantic consistency

Schema shape validation is not sufficient before boundary state influences authorization or verification.

Readers also require deterministic consistency between targets, authority projection, `crossBoundary`, unresolved state, and each target's governing spec chain.

A shape-valid document with unknown `primaryAuthority` never grants implementation permission.

## Target discovery

Target discovery becomes more precise as a feature advances.

Planning may discover paths from explicit implementation structure in `plan.md`. Task generation refines the boundary from exact ordinary task write targets. Authorization uses the existing task-stage boundary without regenerating it. Verification uses actual Git changes rather than current task text.

`.sdd` evolution targets and root SpecDD bootstrap controls remain outside implementation boundary projection.

Pinned SpecDD CLI `1.1.1` requires existing resolver targets. A non-existent intended implementation path therefore remains unresolved with `INTENDED_TARGET_UNSUPPORTED` rather than receiving locally inferred authority.

## Task semantics

Spec Kit remains the canonical feature execution system. SpecDD `Tasks:` entries are local persistent-spec work context and are never synchronized with Spec Kit `tasks.md`.

A normal implementation task should use one primary SpecDD authority when the work is naturally decomposable. User stories may span any number of domains.

A legitimate coordinated task may still write targets owned by several authorities. This is represented as `MULTI_AUTHORITY_TASK` and is not automatically invalid.

When one task deliberately executes all writes under one authority, task text may declare:

    SPECDD_AUTHORITY: `path/to/authority.sdd`

The declared authority must own or have inherited `Can modify` permission for every ordinary write target. Non-owning permission never transfers target ownership.

Task analysis distinguishes:

- `NORMAL`: implementation under current contracts;
- `CROSS_BOUNDARY`: coordinated implementation involving multiple owner domains;
- `SPEC_EVOLUTION`: deliberate persistent contract evolution;
- `AUTHORITY_EVOLUTION`: deliberate ownership or modification-permission evolution.

## Integration layers

The bridge has four architectural layers.

### SpecDD bridge extension

The extension exposes bridge commands, invokes SpecDD tooling, constructs Change Boundaries, validates authority structure, and performs deterministic verification.

The v0.1 command surface is:

- `speckit.specdd.context`;
- `speckit.specdd.validate`;
- `speckit.specdd.authorize`;
- `speckit.specdd.verify`.

### Spec Kit preset

The preset augments planning, task generation, and convergence while preserving upstream command behavior.

It composes with upstream templates rather than copying complete upstream command bodies.

### Workflow overlay

The workflow overlay inserts deterministic structural gates around the upstream `speckit` workflow.

Its resolved sequence is:

    plan
      → specdd-context
      → review-plan
      → tasks
      → specdd-task-validation
      → specdd-authorize
      → implement
      → specdd-verify

### Packaging

The bridge extension, preset, and overlay remain independently sourced under `integration/` and are materialized through supported Spec Kit mechanisms.

Generated `.specify/` and `.agents/skills/` state is not canonical source.

## Thin adapter

The SpecDD adapter stays close to this conceptual API:

    resolve(targets) -> ChangeBoundary
    validate(featureArtifacts, boundary) -> diagnostics
    verify(changes, authorizationEvidence) -> diagnostics

The adapter uses machine-readable SpecDD CLI output and does not become an independent architecture database.

It fails clearly when required tools cannot execute, resolver output is invalid, repository state cannot be identified, or required feature context is absent.

## Deterministic and agentic responsibilities

Objective mechanics belong in deterministic bridge code.

These include:

- invoking `specdd resolve`;
- parsing resolver JSON;
- normalizing repository paths;
- deriving ownership from resolver-returned context;
- evaluating explicit `Can modify` permission;
- checking boundary semantic consistency;
- detecting multi-owner write sets;
- comparing authorization evidence with actual Git state;
- storing and rebuilding derived state;
- detecting context and authorization drift.

Architectural judgment remains agentic when mechanical evidence cannot decide intent.

Examples include:

- whether a multi-owner task should be decomposed;
- whether a proposed path represents an implementation conflict;
- whether a durable contract genuinely needs evolution;
- whether feature information should be promoted into persistent SpecDD.

The bridge should make additional checks deterministic only when doing so does not create a second implementation of SpecDD semantics.

## Progressive strictness

SpecDD strictness increases through the lifecycle.

Planning may tolerate unresolved advisory context while paths are still emerging. Task generation requires structural precision. Authorization fails closed on unknown or stale implementation authority. Verification fails closed when actual writes cannot be reconciled with historical operation evidence.

This permits exploration without weakening implementation authority.
