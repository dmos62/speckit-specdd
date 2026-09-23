# Boundary

Boundary is an integration lab evolving into a standalone persistent-contract and operation-authorization layer for coding agents.

Boundary is not a Spec Kit product and is not a SpecDD product.

The current repository uses:

- Spec Kit as the first change-system adapter because its specification, planning, task, implementation, and convergence workflow is explicit and extensible;
- SpecDD as a temporary persistent-contract compatibility provider while Boundary's native contract model is implemented;
- Codex as the first agent-runtime adapter.

Those integrations are implementation choices. Boundary's durable product concepts are persistent project contracts, scoped applicability, ownership, explicit write scope, operation authorization, progressive agent context, contract evolution, and verification of actual writes.

The target architecture must remain usable if Spec Kit, SpecDD, or Codex is replaced.

## Target model

The intended relationship is:

> The change system owns feature intent and execution state. Boundary owns persistent system contracts and operation authority. Agent adapters deliver the smallest relevant instructions and contract context needed for the current work.

Boundary's target downstream state contains native project contracts such as:

    contracts/auth.contract.md
    contracts/users.contract.md

and one immutable Boundary installation/source pin.

A downstream project must not require:

    .specdd/
    .specdd/bootstrap.md
    specdd
    canonical Boundary implementation source

SpecDD `.sdd` files and `.specdd/` bootstrap state are transitional implementation dependencies in this repository, not part of the target Boundary product.

## Native contracts

Native Boundary contracts use explicit machine-readable scope plus concise human-readable semantics.

A contract may own an exact path or subtree and may apply additional constraints to explicitly scoped paths. Contract location in the repository does not determine its meaning.

Applicable constraints are additive.

A more specific owned subcomponent may become the primary owner of its paths, but broader matching contracts continue to apply. A child contract therefore cannot silently escape a parent contract merely by existing.

Boundary v1 deliberately avoids:

- nearest-contract-wins behavior;
- filesystem-dependent path meaning;
- implicit directory inheritance;
- override or exception semantics;
- a global catch-all cross-contract contract;
- a second persistent compiled copy of project contracts.

Detailed semantics are in [docs/spec-contracts.md](docs/spec-contracts.md).

## Agent instruction model

Boundary does not inject a framework bootstrap or the full project contract set into normal agent context.

Stable procedure is delivered through small skills:

- scope discovery and explicit write declaration;
- implementation under an authorized operation;
- persistent-contract evolution.

Operation-specific facts are queried on demand. For a target, Boundary derives the effective contract context from all matching scoped contracts and relevant interfaces, preserving source provenance.

Project contract prose is therefore progressively disclosed instead of being permanently loaded.

See [docs/spec-agent-instructions.md](docs/spec-agent-instructions.md).

## Authorization model

Authorization uses explicit write declarations from the active change system. Path mentions in planning or task prose are not implementation authority.

At authorization Boundary:

1. reads the exact declared write set;
2. builds the native contract graph fresh;
3. resolves ownership and applicable contracts;
4. validates operation type and Git starting state;
5. records one atomic operation document in current-worktree Git metadata.

Implementation and contract evolution are separate operation kinds.

Verification compares actual post-authorization Git changes with historical operation evidence. Current planning state cannot retroactively widen an operation.

See [docs/spec-authorization.md](docs/spec-authorization.md).

## Lifecycle

Boundary's mandatory implementation lifecycle is intentionally small:

    authorize → implement → verify

Planning and task generation may inspect effective contract context and use Boundary skills, but they do not create authorization state.

A change-system adapter maps its own workflow onto those transitions. The initial Spec Kit adapter is expected to place authorization immediately before implementation and verification immediately after it.

Contract evolution is a separate operation followed by fresh implementation authorization.

See [docs/spec-lifecycle.md](docs/spec-lifecycle.md).

## Current implementation status

The checked-in runtime has not yet completed this migration.

The current implementation still uses:

    integration/specdd/
    integration/specdd-preset/
    .specify/extensions/specdd/
    specs/*/.specdd/boundary.json
    <git-dir>/specdd/

and public commands such as:

    /speckit.specdd.context
    /speckit.specdd.validate
    /speckit.specdd.authorize
    /speckit.specdd.verify

These names and state layouts are transitional. They describe the current executable baseline only and are not the target Boundary architecture.

The active migration plan is in [docs/TODO.md](docs/TODO.md).

## Current compatibility baseline

Until the native migration removes these dependencies, the tested development baseline remains:

| Component | Current requirement |
| --- | --- |
| Node.js | 22+ |
| Spec Kit | `1.0.10` |
| Spec Kit integration | `codex` |
| Stable upstream SpecDD CLI comparison baseline | `1.1.1` |
| Temporary resolver provider | `specdd` package reporting `1.2.0` from `dmos62/specdd-cli` branch `feature/resolve-intended-targets` |
| SpecDD framework | `1.5` |

The stable baseline was re-checked on 2026-09-23.

The temporary SpecDD provider exists only because the current bridge implementation needs typed intended-target resolution. The native Boundary contract engine will remove that dependency rather than standardizing it as a product requirement.

## Current development setup

From this repository checkout:

    bash scripts/bootstrap.sh

Verify the current adapter implementation without intentionally changing repository state:

    bash scripts/bootstrap.sh --check

The bootstrap and installer remain development/migration mechanisms until the Boundary-native downstream workflow is implemented.

Current development and packaging procedures are in [docs/development.md](docs/development.md).

## Design documentation

The target architecture is split by responsibility:

- [docs/spec.md](docs/spec.md): Boundary product model and invariants.
- [docs/spec-architecture.md](docs/spec-architecture.md): core, adapters, transient projections, and implementation boundaries.
- [docs/spec-contracts.md](docs/spec-contracts.md): native contract format, ownership, and additive scoped applicability.
- [docs/spec-agent-instructions.md](docs/spec-agent-instructions.md): skills, progressive disclosure, and cache-friendly agent context.
- [docs/spec-authorization.md](docs/spec-authorization.md): explicit writes, operation evidence, Git baselines, verification, and authorization epochs.
- [docs/spec-lifecycle.md](docs/spec-lifecycle.md): change-system integration, implementation lifecycle, contract evolution, and convergence.
- [docs/change-boundary.md](docs/change-boundary.md): legacy reference for the currently implemented SpecDD-backed Change Boundary model.
- [docs/TODO.md](docs/TODO.md): ordered migration work.
- [docs/TECH-DEBT.md](docs/TECH-DEBT.md): unresolved risks in the current implementation.

The exploratory source that motivated this architecture remains historical guidance rather than an implementation contract.

## Summary invariant

Boundary is correctly designed while this remains true:

> Persistent system constraints are independent of any one change system, contract engine, or agent runtime; agents receive only relevant procedure and effective context; deterministic authorization and verification do not depend on prompt compliance.
