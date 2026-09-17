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

## Development governance versus system contracts

The Spec Kit constitution and the root SpecDD specification intentionally govern different concerns.

The constitution owns development-process rules such as testing expectations, review requirements, migration procedures, compatibility checks, and security-development practices.

The root SpecDD specification owns durable system and product rules such as architecture boundaries, persistent dependency direction, ownership, modification authority, and contracts that future implementation work must preserve.

A rule belongs in the layer matching its meaning. The bridge does not copy constitution rules into `.sdd` files or persistent SpecDD constraints into feature artifacts.

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

Detailed Change Boundary lifecycle semantics are documented in [docs/change-boundary.md](docs/change-boundary.md).

## Normal lifecycle

The normal bridge sequence is:

    context → validate → authorize → implement → verify

The installed Spec Kit workflow overlay enforces the corresponding lifecycle structurally:

    plan
      → specdd-context
      → review-plan
      → tasks
      → specdd-task-validation
      → specdd-authorize
      → implement
      → specdd-verify

Agent lifecycle hooks remain useful when bridge commands are invoked directly. They provide command-level context and reporting, but they are not the deterministic enforcement boundary. The workflow overlay executes bridge scripts as shell gates, so error or blocking diagnostics can stop workflow execution.

## Bridge command usage

The four bridge commands share the active Spec Kit feature but have different authority semantics.

| Command | Inputs and target discovery | Result |
| --- | --- | --- |
| `/speckit.specdd.context` | Explicit non-`.sdd` target arguments take precedence; otherwise exact targets come from `tasks.md`, then `plan.md`. | Rebuilds `.specdd/boundary.json` from fresh SpecDD resolution. If no concrete target exists, stale boundary state is removed instead of reused. |
| `/speckit.specdd.validate` | Uses the existing boundary and `tasks.md`. Optional stage is `planning`, `tasks`, or `implementation`; default is `tasks`. | Reports task authorities, unresolved or stale scope, multi-authority tasks, and explicit specification-evolution structure. It does not rewrite tasks. |
| `/speckit.specdd.authorize` | Uses the existing boundary and `tasks.md` at implementation strictness. | Blocks implementation when current scope has stale, unknown, conflicting, or otherwise unauthorized authority. It never refreshes the boundary. |
| `/speckit.specdd.verify` | Uses actual Git changes, the existing planned boundary, fresh SpecDD resolution for existing implementation targets, and `specdd lint`. | Reports authority violations, unplanned same-domain drift, specification changes, control-state changes, and SpecDD lint failures without changing repository state. |

Typical direct invocations are:

    /speckit.specdd.context
    /speckit.specdd.validate tasks
    /speckit.specdd.authorize
    /speckit.specdd.verify

The task-stage structural workflow gate deliberately refreshes the boundary from finalized task targets before validation. Authorization and verification deliberately do not refresh it because the existing file is the implementation operation's authority snapshot.

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

A task that touches several authorities is not automatically invalid. The bridge reports authority groups so naturally separable work can become authority-local tasks while remaining under the same feature and user story.

Legitimate cross-domain contract work can remain together when the current authority model permits every write and decomposition would reduce coherence.

What the bridge must not do is relax SpecDD authority merely to make a task pass.

## Specification evolution

Some features require a durable system-contract change rather than ordinary implementation under existing contracts.

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

## Diagnostics

Deterministic diagnostics describe structural facts. Architectural conclusions such as whether a durable contract must evolve remain separate agentic judgments.

| Diagnostic | Meaning |
| --- | --- |
| `INVALID_TARGET` | Input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | A valid target has no trustworthy current authority projection. |
| `RESOLUTION_FAILED` | SpecDD resolution failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | Multiple resolved specifications claim ownership of a target. |
| `MULTI_AUTHORITY_TASK` | One task spans several authority domains. This is a warning, not automatic invalidity. |
| `STALE_BOUNDARY` | Active feature or current task scope no longer matches the planned boundary. |
| `AUTHORITY_VIOLATION` | Implementation authority is unknown, conflicting, changed, or outside the planned authority set. |
| `EVOLUTION_CLASSIFICATION_CONFLICT` | One task declares both supported evolution classifications. |
| `EVOLUTION_SPEC_TARGET_REQUIRED` | An evolution task does not identify a `.sdd` target. |
| `EVOLUTION_SCOPE_MIXED` | One task mixes specification evolution with ordinary implementation writes. |
| `SPECDD_DRIFT` | An actual implementation write was unplanned but remains inside an already planned authority domain. |
| `SPECDD_VIOLATION` | The resulting repository fails deterministic SpecDD checks such as `specdd lint`. |
| `SPEC_EVOLUTION_PRESENT` | `.sdd` changes exist; this is informational and grants no implementation authority. |
| `CONTROL_STATE_CHANGED` | SpecDD bootstrap control state changed and requires explicit review. |

`MISSING_SPEC_EVOLUTION` is intentionally different: it is an architectural finding used when implementation introduces a durable system contract that future work must preserve but corresponding deliberate SpecDD evolution is absent.

## Troubleshooting

If bootstrap reports that the bridge extension, preset, commands, or workflow overlay are missing, run:

    bash scripts/bootstrap.sh

Check mode intentionally verifies existing generated state rather than materializing missing state.

If `specdd` is unavailable or the installed CLI is not version `1.1.1`, run repository bootstrap rather than bypassing the bridge. Bootstrap installs the pinned CLI and verifies the framework version before bridge checks continue.

If the Codex integration is unavailable or `codex` is not on `PATH`, install the Codex CLI before bootstrap. Pinned Spec Kit `1.0.7` cannot use the `generic` integration as a substitute for registrar-backed bridge commands.

If a Change Boundary reports `UNRESOLVED_TARGET`, first confirm that the intended implementation path is correct and that its governing SpecDD chain provides clear ownership. A target that does not yet exist may remain unresolved during early planning, but implementation requires trustworthy authority.

If a target reports `AMBIGUOUS_AUTHORITY`, resolve the competing ownership claims rather than choosing the nearest spec or inferring ownership from directory names.

If task validation reports `STALE_BOUNDARY`, refresh context from finalized task paths before authorization.

If authorization reports stale or unknown authority, implementation remains blocked under that snapshot. Refresh before implementation only after the underlying task or specification operation has been corrected; do not refresh inside the authorization gate itself.

## Project documentation

The durable project design is in [docs/spec.md](docs/spec.md).

Focused Change Boundary lifecycle semantics are in [docs/change-boundary.md](docs/change-boundary.md).

Development-host setup and maintenance procedures are in [docs/development.md](docs/development.md).

Remaining implementation work is tracked in [docs/TODO.md](docs/TODO.md).
