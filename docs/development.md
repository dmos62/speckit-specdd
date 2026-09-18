# Development Setup

This repository is an integration lab for Spec Kit and SpecDD. Keep upstream-generated state separate from bridge
source and keep the toolchain pinned while v0.1 semantics are being proven.

## Compatibility baseline

Selected on 2026-09-17:

| Component | v0.1 requirement | Direct evidence |
| --- | --- | --- |
| Node.js | 22+ | Runtime prerequisite; bootstrap reports the exact Node version used by each check run. |
| uv | installed | Required by supported Spec Kit and bridge command paths. |
| Spec Kit | `1.0.7` | Bootstrap, installation, preset composition, workflow overlay, and tests pass at this exact version. |
| Spec Kit integration | `codex` | Registrar-backed integration exercised by installation smoke tests and bootstrap. |
| SpecDD CLI | `1.1.1` | Resolver fixtures, validation, verification, lint, bootstrap, and install tests pass at this version. |
| SpecDD framework | `1.5` | Repository and fixture specs lint cleanly at this exact framework version. |

The compatibility range is intentionally a singleton for Spec Kit, SpecDD CLI, and the SpecDD framework.

The 2026-09-17 evidence host was Windows 10 `10.0.19045` on AMD64, and Spec Kit reported Python `3.12.11`. Those values
describe the exercised host, not a supported range.

## Prerequisites

Install Git, Node.js 22+, npm, uv, and the Codex CLI.

With nvm:

    nvm install
    nvm use

The active Spec Kit integration requires `codex` on `PATH`.

## Bootstrap

From the repository root:

    bash scripts/bootstrap.sh

Bootstrap verifies prerequisites, installs the pinned Spec Kit and SpecDD versions, activates the Codex integration,
installs the local extension/preset/workflow overlay, runs Spec Kit checks, and runs `specdd lint`.

Bootstrap refuses to rewrite an existing SpecDD bootstrap whose framework version differs from `1.5`.

Do not manually patch `.specify/`, `.agents/skills/`, `.specify-agent/commands/`, or root `.specdd/` framework state.

## Rematerialize bridge source

When only canonical bridge source changed:

    specify integration switch codex --script ps
    specify extension add integration/specdd --dev --force
    specify preset remove specdd-bridge || true
    specify preset add --dev integration/specdd-preset --priority 10
    specify workflow overlay remove speckit specdd-bridge || true
    specify workflow overlay add integration/specdd/workflow-overlay.yml --priority 10

Verify installed state with:

    specify extension list --json
    specify preset list
    specify workflow overlay list speckit
    specify workflow resolve speckit
    bash scripts/bootstrap.sh --check

## Structural workflow enforcement

Canonical workflow-overlay source is:

    integration/specdd/workflow-overlay.yml

The installed copy under `.specify/workflows/overlays/` is generated state.

The resolved `speckit` workflow adds four deterministic shell steps:

- `specdd-context` refreshes advisory feature Change Boundary context after planning.
- `specdd-task-validation` refreshes ordinary implementation scope from exact task targets and validates it.
- `specdd-authorize` validates the existing boundary and records immutable operation evidence.
- `specdd-verify` compares post-authorization Git state with that historical evidence.

Authorization evidence consists of the exact validated boundary, a fingerprint-bound companion plan, and a
fingerprint-bound Git baseline. The companion records exact planned `.sdd` evolution targets and exact editable
bootstrap overrides selected before implementation. The Git baseline records authorization-time `HEAD` plus
content/deletion identities for every dirty path.

A later Change Boundary refresh or task edit cannot change this historical evidence. Verification excludes unchanged
pre-authorization dirty state, but any path changed after authorization remains in operation scope. If Git `HEAD`
changes, verification fails closed and requires fresh authorization. Optional feature worktrees can isolate concurrent
operations but are not part of SpecDD authority semantics.

## Bootstrap control state

Root SpecDD bootstrap files are control state, not ordinary bridge implementation targets.

`.specdd/bootstrap.md` is immutable.

`.specdd/bootstrap.project.md` is shared project control state and may change only when explicitly selected by the
Operator or authorized workflow before implementation. Authorization records that selection.

`.specdd/bootstrap.local.md` remains local/generated preference state. It may be explicitly selected locally but stays
outside shared implementation-write verification and is excluded from iteration context.

Unrelated root `.specdd/` changes are never inferred as permitted implementation work.

## Verify without changing canonical source

For subsequent iterations:

    bash scripts/bootstrap.sh --check

For workflow inspection:

    specify workflow overlay list speckit
    specify workflow resolve speckit

The resolved workflow should place SpecDD context after `plan`, task validation after `tasks`, authorization before
`implement`, and verification after `implement`.

## Generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Spec Kit materializes installed commands and bookkeeping under `.agents/skills/` and `.specify/`. Treat those outputs as
generated integration state.

Feature Change Boundaries are generated feature state. Refresh-time effective-context evidence, authorization boundary
snapshots, companion operation selections, and authorization-time Git baselines are generated current-worktree Git
metadata.

SpecDD local operator preferences remain in `.specdd/bootstrap.local.md` and are excluded from shared iteration context.

## Baseline review

After bootstrap or deliberate integration migration:

    git status --short
    bash scripts/bootstrap.sh --check

Review generated `.specify/`, `.agents/skills/`, feature `.specdd/`, and root `.specdd/` state according to repository
policy. Keep canonical bridge changes under `integration/`.

The clean-clone acceptance gate also checks the full tests, fixture lint, patch integrity, unexpected canonical-source
changes, and tracked files accidentally covered by ignore rules.
