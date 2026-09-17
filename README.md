# Spec Kit × SpecDD Bridge

This repository is an integration lab for using GitHub Spec Kit and SpecDD together without merging, forking, or duplicating either system.

Spec Kit owns the lifecycle of a change: feature specification, planning, task generation, implementation, and convergence.

SpecDD owns the persistent model of the system: hierarchical specifications, ownership, modification authority, dependencies, local contracts, and architectural constraints.

The bridge projects the relevant SpecDD authority into each Spec Kit feature so feature work can be planned and implemented within the system contracts that already exist.

## Responsibility split

The central rule is:

> Spec Kit owns the change model. SpecDD owns the persistent system model. The bridge projects the latter onto the former without creating a third source of truth.

In practice:

- `spec.md`, `plan.md`, and `tasks.md` describe the current feature and its implementation work.
- `.sdd` files describe durable system structure and contracts that future work must continue to respect.
- The Spec Kit constitution governs how development is performed.
- The bridge derives temporary integration state from those canonical artifacts.

Spec Kit tasks are not synchronized with SpecDD `Tasks:` entries. They serve different purposes: Spec Kit tasks execute a feature, while SpecDD tasks are local planning context for a durable system contract.

## Compatibility

The v0.1 development baseline is intentionally pinned:

| Component | Version |
| --- | --- |
| Node.js | 22.x or newer |
| Spec Kit | 1.0.7 |
| Spec Kit integration | `codex` |
| SpecDD CLI | 1.1.1 |
| SpecDD framework | 1.5 |

Pinned Spec Kit `1.0.7` does not register the bridge commands through the `generic` integration. This repository therefore uses the registrar-backed `codex` integration.

Do not silently advance these versions during v0.1 work.

## Install

The normal local installation path is:

    bash scripts/bootstrap.sh

Bootstrap installs or verifies the pinned toolchain, initializes Spec Kit and SpecDD when necessary, activates the Codex integration, installs the local bridge extension and preset, materializes the structural workflow overlay, and runs the repository health checks.

After installation, verify the current state without changing it:

    bash scripts/bootstrap.sh --check

Detailed host prerequisites, integration switching, development rematerialization, and maintenance commands are documented in [docs/development.md](docs/development.md).

## Canonical source and generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Spec Kit materializes installed commands and integration state under locations such as:

    .agents/skills/
    .specify/extensions/
    .specify/presets/
    .specify/workflows/

Those locations are generated integration state. Do not hand-edit them to change bridge behavior. Change the canonical source and reinstall through supported Spec Kit commands or repository bootstrap.

Root `.specdd/` framework state is likewise not an implementation surface for the bridge.

## Change Boundary

A Change Boundary is a derived, feature-scoped projection of SpecDD authority onto the implementation paths of one Spec Kit feature.

For a feature directory such as:

    specs/001-google-login/

the bridge stores derived state at:

    specs/001-google-login/.specdd/boundary.json

A boundary records information such as:

- resolved implementation targets,
- each target's primary SpecDD authority,
- the distinct authority domains involved,
- whether the feature crosses authority domains,
- unresolved or ambiguous targets,
- deterministic generation metadata.

The boundary is not another specification file and does not contain a persistent copy of SpecDD rules.

It is safe to regenerate. The `.sdd` hierarchy remains authoritative.

As planning becomes more concrete, the bridge can refresh the boundary from more precise implementation paths. Unresolved early planning scope is advisory; unresolved implementation authority is not permission.

## Normal lifecycle

The bridge exposes four commands:

| Command | Purpose |
| --- | --- |
| `/speckit.specdd.context` | Build or refresh the feature Change Boundary. |
| `/speckit.specdd.validate` | Validate task write scope against the current boundary. |
| `/speckit.specdd.authorize` | Gate implementation against the existing authority snapshot. |
| `/speckit.specdd.verify` | Compare actual Git writes with the planned authority snapshot and fresh SpecDD resolution. |

The normal sequence is:

    context → validate → authorize → implement → verify

The installed Spec Kit workflow overlay enforces the same lifecycle structurally:

    plan
      → specdd-context
      → review-plan
      → tasks
      → specdd-task-validation
      → specdd-authorize
      → implement
      → specdd-verify

Agent lifecycle hooks remain useful for command-level context and reporting, but the workflow overlay is the deterministic enforcement boundary. Its shell steps propagate failing validation or verification status through the Spec Kit workflow.

## Authority and cross-domain work

One feature may legitimately span multiple SpecDD authority domains.

For example, the repository fixture contains separate Auth and Users domains:

    Auth
      src/auth/service.ts
        authority: src/auth/auth.sdd

    Users
      src/users/identity-contract.ts
      src/users/repository.ts
        authority: src/users/users.sdd

A feature such as external-identity login can remain one Spec Kit user story while its implementation is divided into authority-local work:

- Auth changes authentication behavior in `src/auth/service.ts`.
- Users changes its contract or persistence behavior in Users-owned files.
- Cross-domain interaction uses the Users-facing contract rather than treating Users internals as Auth-owned implementation.

A task that touches several authorities is not automatically invalid. The bridge reports the authority groups so an agent can decide whether the work should be decomposed or is legitimate cross-domain contract work.

What the bridge must not do is relax SpecDD authority merely to make a task pass.

## Specification evolution

Some features require a durable system-contract change rather than ordinary implementation under the existing contracts.

The bridge distinguishes:

- normal implementation under current SpecDD contracts,
- `SPEC_EVOLUTION_REQUIRED`,
- `AUTHORITY_EVOLUTION_REQUIRED`.

Specification evolution is deliberately separate from implementation authority.

If an `.sdd` change is required:

1. identify and apply the specification change as its own operation;
2. end the previous authority context when authority itself changed;
3. refresh `/speckit.specdd.context`;
4. begin dependent implementation under the newly resolved boundary.

A changed `.sdd` file never retroactively authorizes implementation writes made in the same operation.

This authority-snapshot invariant prevents a task from granting itself new permissions and immediately relying on them.

## Validation and verification findings

Common deterministic findings include:

- `UNRESOLVED_TARGET` — no trustworthy authority projection exists for a target.
- `MULTI_AUTHORITY_TASK` — one task spans multiple authority domains; this is a warning rather than automatic invalidity.
- `STALE_BOUNDARY` — feature or task scope no longer matches the current projection.
- `AUTHORITY_VIOLATION` — implementation authority is unknown, conflicting, changed, or outside the planned authority set.
- `SPECDD_DRIFT` — an actual implementation write was unplanned but remains inside an already planned authority domain.
- `SPECDD_VIOLATION` — the resulting repository fails deterministic SpecDD checks.
- `SPEC_EVOLUTION_PRESENT` — `.sdd` changes exist; this is informational and does not grant implementation authority.

Architectural findings such as `MISSING_SPEC_EVOLUTION` remain separate from deterministic authority calculations because deciding whether an implementation introduces a durable contract can require architectural judgment.

## Troubleshooting

If bootstrap reports that the bridge extension, preset, commands, or workflow overlay are missing, run:

    bash scripts/bootstrap.sh

Check mode intentionally verifies existing generated state rather than materializing missing state.

If the Codex integration is unavailable or `codex` is not on `PATH`, install the Codex CLI before bootstrap. Pinned Spec Kit `1.0.7` cannot use the `generic` integration as a substitute for registrar-backed bridge commands.

If a Change Boundary reports `UNRESOLVED_TARGET`, first confirm that the intended implementation path is correct and that its governing SpecDD chain provides clear ownership. A target that does not yet exist may remain unresolved during early planning, but implementation requires trustworthy authority.

If a target reports `AMBIGUOUS_AUTHORITY`, resolve the competing ownership claims rather than choosing the nearest spec or inferring ownership from directory names.

If authorization reports stale scope, refresh the boundary before implementation rather than weakening the gate.

## Project documentation

The durable project design is in [docs/spec.md](docs/spec.md).

Development-host setup and maintenance procedures are in [docs/development.md](docs/development.md).

Remaining implementation and documentation work is tracked in [docs/TODO.md](docs/TODO.md).
