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

The v0.1 baseline is deliberately narrow.

| Component | Requirement |
| --- | --- |
| Node.js | 22+ |
| Spec Kit | `1.0.7` |
| Spec Kit integration | `codex` |
| SpecDD CLI | `1.1.1` |
| SpecDD framework | `1.5` |

The exercised 2026-09-17 host was Windows 10 `10.0.19045` on AMD64 with Python `3.12.11`. Those observations are test
evidence, not broader compatibility claims.

Pinned Spec Kit `1.0.7` does not register these bridge commands through the `generic` integration, so the repository
uses the registrar-backed `codex` integration.

## Install

Run:

    bash scripts/bootstrap.sh

Then verify without intentionally changing repository state:

    bash scripts/bootstrap.sh --check

Host prerequisites, rematerialization, and maintenance procedures are in
[docs/development.md](docs/development.md).

## Canonical source and generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Generated Spec Kit integration state lives under locations such as:

    .agents/skills/
    .specify/

Do not hand-edit generated integration state. Change canonical source and reinstall through supported Spec Kit commands.

Root `.specdd/` framework state is likewise not an implementation surface for the bridge.

## Change Boundary and authorization snapshot

The bridge uses two different derived states.

A feature Change Boundary is refreshable planning and task context:

    specs/001-google-login/.specdd/boundary.json

It records resolved implementation targets, primary authorities, governing specs, authority domains, cross-boundary
status, unresolved diagnostics, and deterministic tool-version metadata.

Pinned SpecDD CLI `1.1.1` resolves existing targets only. A non-existent intended target is retained as
`UNRESOLVED_TARGET` with an `INTENDED_TARGET_UNSUPPORTED` message rather than receiving authority inferred by the bridge.
This indicates a current tool limitation, not a SpecDD prohibition on creating the file. Planning may carry that
uncertainty, but task validation and implementation authorization fail closed until resolver-backed authority exists.

A successful authorization copies the exact validated Change Boundary into immutable operation evidence stored in the
current worktree Git metadata:

    <git-dir>/specdd/authorization-boundary.json

Refreshing the feature Change Boundary does not change the authorization snapshot.

This distinction prevents specification or context changes during implementation from retroactively changing the
authority under which that implementation operation is verified.

Detailed lifecycle semantics are in [docs/change-boundary.md](docs/change-boundary.md).

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

The stages have distinct responsibilities:

| Stage | Responsibility |
| --- | --- |
| context | Refresh current feature scope from concrete non-`.sdd` targets. |
| validate | Check task scope against the current boundary. |
| authorize | Validate implementation scope and record an immutable authorization snapshot. |
| implement | Change project artifacts only within the authorized operation. |
| verify | Compare actual Git writes with the authorization snapshot and fresh SpecDD resolution. |

Agent lifecycle hooks remain useful for direct command execution and interpretation. Structural workflow shell gates are
the deterministic failure boundary.

## Bridge commands

Typical direct invocations are:

    /speckit.specdd.context
    /speckit.specdd.validate tasks
    /speckit.specdd.authorize
    /speckit.specdd.verify

`/speckit.specdd.context` refreshes feature boundary state. Explicit target arguments take precedence; otherwise exact
targets come from `tasks.md`, then `plan.md`.

`/speckit.specdd.validate` checks tasks against the current boundary at planning, task, or implementation strictness. It
does not create authorization.

`/speckit.specdd.authorize` preserves the current boundary, validates it at implementation strictness, and records the
validated result as the current operation's authorization snapshot.

`/speckit.specdd.verify` ignores later boundary refreshes as authority evidence. It uses actual Git changes, the
authorization snapshot, fresh SpecDD resolution for existing implementation targets, and `specdd lint`.

## Cross-domain work

One feature may legitimately span several SpecDD authority domains.

The fixture contains independent Auth and Users domains. An external-identity feature can remain one Spec Kit user story
while implementation work is divided into authority-local tasks:

- Auth changes `src/auth/service.ts`.
- Users changes Users-owned contract or persistence files.
- cross-domain interaction uses the exposed Users-facing contract.

A task touching several authorities is not automatically invalid. The bridge reports authority groups so naturally
separable work can become authority-local without splitting the user story.

The bridge must not relax SpecDD authority merely to make a task pass.

## Specification evolution

Some features require durable system-contract evolution.

The bridge distinguishes ordinary implementation from:

- `SPEC_EVOLUTION_REQUIRED`;
- `AUTHORITY_EVOLUTION_REQUIRED`.

Specification evolution is separate from implementation authority.

When dependent implementation requires an `.sdd` change:

1. complete the specification change as its own operation;
2. end the old authority context when authority itself changed;
3. refresh `/speckit.specdd.context`;
4. run `/speckit.specdd.authorize` successfully;
5. begin dependent implementation under the new authorization snapshot.

A changed `.sdd` file or refreshed Change Boundary never retroactively authorizes implementation already performed.

## Diagnostics

Core deterministic diagnostics include:

| Diagnostic | Meaning |
| --- | --- |
| `INVALID_TARGET` | Input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | A valid target lacks trustworthy current authority projection. For a non-existent target, `INTENDED_TARGET_UNSUPPORTED` in the message identifies the pinned CLI limitation. |
| `RESOLUTION_FAILED` | SpecDD resolution failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | Multiple resolved specifications claim ownership. |
| `MULTI_AUTHORITY_TASK` | One task spans several authority domains. |
| `STALE_BOUNDARY` | Feature or task scope disagrees with the current boundary or snapshot. |
| `AUTHORITY_VIOLATION` | Actual or proposed implementation authority is unknown, conflicting, changed, or outside authorized scope. |
| `SPECDD_DRIFT` | An actual target was not authorized even though its authority domain was authorized. |
| `SPECDD_VIOLATION` | Resulting repository state fails deterministic SpecDD checks. |
| `SPEC_EVOLUTION_PRESENT` | `.sdd` changes exist and grant no authority to the current operation. |
| `CONTROL_STATE_CHANGED` | SpecDD bootstrap control state changed and requires separate review. |

`MISSING_SPEC_EVOLUTION` remains an architectural finding rather than a path-only deterministic result.

## Project documentation

- [docs/spec.md](docs/spec.md): durable project design.
- [docs/change-boundary.md](docs/change-boundary.md): Change Boundary and authorization-snapshot lifecycle.
- [docs/development.md](docs/development.md): development environment and maintenance.
- [docs/TODO.md](docs/TODO.md): active implementation work.
