# Spec Kit × SpecDD Bridge

This repository is an integration lab for using GitHub Spec Kit and SpecDD together without merging, forking, or
duplicating either system.

Spec Kit owns the lifecycle of a change: feature specification, planning, task generation, implementation, and
convergence.

SpecDD owns the persistent model of the system: hierarchical specifications, ownership, modification authority,
dependencies, local contracts, and architectural constraints.

The bridge projects current SpecDD authority into each Spec Kit feature so feature work can be planned and implemented
inside the system contracts that already exist.

## Responsibility split

The central rule is:

> Spec Kit owns the change model. SpecDD owns the persistent system model. The bridge projects the latter onto the former without creating a third source of truth.

In practice:

- `spec.md`, `plan.md`, and `tasks.md` describe the current feature and implementation work.
- `.sdd` files describe durable system structure and contracts future work must preserve.
- the Spec Kit constitution governs development process.
- the bridge derives temporary integration state from those canonical artifacts.

Spec Kit tasks are not synchronized with SpecDD `Tasks:` entries.

## Compatibility

| Component | Requirement |
| --- | --- |
| Node.js | 22+ |
| Spec Kit | `1.0.7` |
| Spec Kit integration | `codex` |
| SpecDD CLI | `1.1.1` |
| SpecDD framework | `1.5` |

The exercised 2026-09-17 host was Windows 10 `10.0.19045` on AMD64 with Python `3.12.11`. Those observations are test
evidence, not broader compatibility claims.

## Install

Run:

    bash scripts/bootstrap.sh

Then verify without intentionally changing repository state:

    bash scripts/bootstrap.sh --check

Development procedures are in [docs/development.md](docs/development.md).

## Canonical source and generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Generated Spec Kit integration state lives under locations such as:

    .agents/skills/
    .specify/

Do not hand-edit generated integration state. Root `.specdd/` framework state is also not an ordinary bridge
implementation surface.

## Change Boundary and authorization evidence

A feature Change Boundary is refreshable planning/task context:

    specs/001-google-login/.specdd/boundary.json

It records ordinary implementation targets, primary owners, governing specs, authority domains, cross-boundary status,
unresolved diagnostics, and deterministic tool-version metadata. It does not copy `Can modify` rules.

An unmarked multi-owner task remains coordinated across its owning domains. When one task intentionally performs all
writes under one authority, task text uses `SPECDD_AUTHORITY:` and validation fresh-resolves non-owning `Can modify`
permission while preserving each target's original owner.

Pinned SpecDD CLI `1.1.1` resolves existing targets only. Missing intended implementation targets remain
`UNRESOLVED_TARGET` with `INTENDED_TARGET_UNSUPPORTED` rather than receiving locally inferred authority.

Successful authorization stores two immutable operation-evidence documents in current-worktree Git metadata:

    <git-dir>/specdd/authorization-boundary.json
    <git-dir>/specdd/authorization-spec-evolution.json

The first is the exact validated Change Boundary. The fingerprint-bound companion document records exact `.sdd`
evolution targets plus exact editable bootstrap overrides selected before implementation.

Bootstrap-control selections record whether they came from an authorized workflow task or direct Operator selection.
They do not grant implementation authority.

Refreshing the feature Change Boundary or later editing `tasks.md` does not change authorization evidence.

## Bootstrap controls

Root SpecDD bootstrap files follow separate control rules rather than Change Boundary ownership:

- `.specdd/bootstrap.md` is immutable.
- `.specdd/bootstrap.project.md` may change only after explicit workflow or Operator selection is recorded by
  authorization.
- `.specdd/bootstrap.local.md` remains local/generated preference state.
- unrelated root `.specdd/` state is not implicitly editable.

Verification blocks immutable, unrelated, and unplanned shared control changes. A deliberately selected project override
is reported separately from implementation writes.

## Normal lifecycle

The bridge sequence is:

    context → validate → authorize → implement → verify

The installed workflow overlay enforces:

    plan
      → specdd-context
      → review-plan
      → tasks
      → specdd-task-validation
      → specdd-authorize
      → implement
      → specdd-verify

| Stage | Responsibility |
| --- | --- |
| context | Refresh current ordinary implementation scope. |
| validate | Check task ownership and applicable modification permission. |
| authorize | Record immutable boundary, evolution, and control-selection evidence. |
| implement | Change project artifacts only within the authorized operation. |
| verify | Compare actual Git state with historical evidence and fresh SpecDD resolution. |

## Bridge commands

Typical direct invocations are:

    /speckit.specdd.context
    /speckit.specdd.validate tasks
    /speckit.specdd.authorize
    /speckit.specdd.verify

`context` refreshes ordinary implementation boundary state.

`validate` checks tasks against current ownership and `Can modify` projection. Root bootstrap controls are reported
separately from implementation targets.

`authorize` preserves the current boundary and records exact explicit specification/control selections before
implementation.

`verify` ignores later boundary/task changes as authorization evidence and uses actual Git changes, historical evidence,
fresh SpecDD resolution, and `specdd lint`.

## Cross-domain work

One feature may legitimately span several SpecDD owner domains.

The fixture contains independent Auth and Users domains. Auth owns its service, Users owns its identity contract and
repository, and Auth has explicit `Can modify` permission only for the Users-facing identity contract.

A `MULTI_AUTHORITY_TASK` warning describes ownership shape, not invalidity. A declared operation authority makes
non-owning permission deterministic through `operationAuthorities` and `modificationPermissions`.

## Specification evolution

Some features require durable system-contract evolution. The bridge distinguishes ordinary implementation from
`SPEC_EVOLUTION_REQUIRED` and `AUTHORITY_EVOLUTION_REQUIRED`.

When dependent implementation requires `.sdd` evolution:

1. complete specification work separately;
2. end the old authority context when authority changed;
3. refresh context;
4. authorize again;
5. begin dependent implementation under new evidence.

Changed `.sdd`, bootstrap-control, or Change Boundary state never retroactively authorizes implementation already
performed.

## Diagnostics

| Diagnostic | Meaning |
| --- | --- |
| `INVALID_TARGET` | Input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | A target lacks trustworthy current authority projection. |
| `RESOLUTION_FAILED` | SpecDD resolution failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | Multiple resolved specifications claim ownership. |
| `MULTI_AUTHORITY_TASK` | One task contains targets owned by several authority domains. |
| `STALE_BOUNDARY` | Current scope disagrees with the boundary or snapshot. |
| `AUTHORITY_VIOLATION` | Proposed or actual implementation has invalid authority. |
| `SPECDD_DRIFT` | An actual target was not authorized though its authority domain was. |
| `SPECDD_VIOLATION` | Resulting repository state fails deterministic SpecDD checks. |
| `SPEC_EVOLUTION_PRESENT` | Changed `.sdd` files were selected at authorization. |
| `UNPLANNED_SPEC_EVOLUTION` | Changed `.sdd` files were not selected at authorization. |
| `CONTROL_STATE_CHANGED` | A selected project bootstrap override changed. |
| `CONTROL_STATE_VIOLATION` | Immutable, unrelated, or unplanned root SpecDD control state changed. |

`MISSING_SPEC_EVOLUTION` remains an architectural finding rather than a path-only deterministic result.

## Project documentation

- [docs/spec.md](docs/spec.md): durable project design.
- [docs/change-boundary.md](docs/change-boundary.md): boundary, authorization, and lifecycle semantics.
- [docs/development.md](docs/development.md): development environment and maintenance.
- [docs/TODO.md](docs/TODO.md): active implementation work.
