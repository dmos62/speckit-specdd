# Development Setup

This repository is an integration lab for Spec Kit and SpecDD. Keep upstream-generated state separate from bridge source and keep the toolchain pinned while v0.1 semantics are being proven.

## Compatibility baseline

Selected on 2026-09-17:

| Component | Pin | Reason |
| --- | --- | --- |
| Node.js | 22.x or newer | SpecDD CLI requires Node.js 22+; `.nvmrc` selects the minimum supported major. |
| uv | installed on the development host | Required for the supported Spec Kit installation path. |
| Spec Kit | 1.0.7 | Current stable release selected for v0.1 development. |
| Spec Kit integration | `codex` | Registrar-backed integration used to materialize extension and preset commands under `.agents/skills`. |
| SpecDD CLI | 1.1.1 | Current stable CLI release selected for v0.1 development. |
| SpecDD framework | 1.5 | Current framework release selected for authority semantics and bootstrap behavior. |

Pinned Spec Kit `1.0.7` deliberately excludes the `generic` integration from its command registrar. The repository therefore uses the Codex integration for executable bridge commands instead of patching generated generic command files.

Upstream references used for this baseline:

- Spec Kit releases: https://github.com/github/spec-kit/releases
- Spec Kit installation: https://github.com/github/spec-kit/blob/main/docs/installation.md
- Spec Kit integrations: https://github.com/github/spec-kit/blob/main/docs/reference/integrations.md
- SpecDD CLI: https://github.com/specdd/cli
- SpecDD framework releases: https://github.com/specdd/specdd/releases

Do not silently advance these pins during v0.1. Upgrade them only as a deliberate compatibility task with the fixture and acceptance tests rerun.

## Prerequisites

Install Git, Node.js 22+, npm, uv, and the Codex CLI before running repository bootstrap.

With nvm, activate the repository-selected Node major with:

    nvm install
    nvm use

Install uv using the official instructions for the development host if `uv --version` is unavailable.

The active Spec Kit integration requires `codex` to be available on `PATH`. Bootstrap fails explicitly when it is absent rather than falling back to an integration that cannot register bridge commands.

## Bootstrap

From the repository root, run:

    bash scripts/bootstrap.sh

The script:

- verifies Git, Node.js, npm, uv, and Codex,
- installs Spec Kit 1.0.7 with `uv tool`,
- installs SpecDD CLI 1.1.1 with npm,
- initializes Spec Kit with the Codex integration, or migrates an existing initialized repository with `specify integration switch codex`,
- initializes SpecDD framework 1.5,
- installs the local bridge extension from `integration/specdd/` in development mode,
- installs the local bridge preset from `integration/specdd-preset/` in development mode,
- installs the structural SpecDD workflow overlay from `integration/specdd/workflow-overlay.yml`,
- verifies bridge commands under `.agents/skills`,
- verifies lifecycle hook registration, preset command materialization, and resolved workflow gates,
- runs the Spec Kit environment check,
- runs `specdd lint`.

The script intentionally refuses to rewrite an existing SpecDD bootstrap whose framework version differs from 1.5. Review such a version change explicitly instead of allowing bootstrap automation to mutate system semantics unexpectedly.

Integration switching, extension installation, preset installation, and workflow-overlay installation are performed through supported Spec Kit commands. Do not manually patch `.specify/`, `.agents/skills/`, `.specify-agent/commands/`, or root `.specdd/` framework state to expose the bridge.

## Structural workflow enforcement

Canonical workflow-overlay source is:

    integration/specdd/workflow-overlay.yml

Bootstrap installs it with `specify workflow overlay add`. The installed copy under `.specify/workflows/overlays/` is generated state and must not be hand-edited.

The resolved `speckit` workflow adds four deterministic shell steps:

- `specdd-context` runs after planning and refreshes advisory Change Boundary context from explicit plan paths when available.
- `specdd-task-validation` runs after task generation, refreshes the boundary from exact non-spec task targets, and fails the workflow on deterministic error or blocking diagnostics.
- `specdd-authorize` runs immediately before implementation against that existing boundary. It does not refresh authority and fails on deterministic error or blocking diagnostics.
- `specdd-verify` runs after implementation against the planned boundary plus fresh resolution of actual Git writes. Deterministic error or blocking diagnostics fail the workflow.

These shell steps omit `continue_on_error`, so nonzero status propagates through the Spec Kit workflow engine and halts execution.

Extension lifecycle hooks remain useful for direct command execution, agent-facing reporting, decomposition guidance, and architectural interpretation. They are not the structural enforcement mechanism. The workflow overlay calls deterministic bridge scripts directly rather than relying on hook-dispatch compliance for failure propagation.

## Verify without changing the repository

Use check mode for subsequent iterations:

    bash scripts/bootstrap.sh --check

Check mode verifies the pinned tool versions, active Codex integration, materialized bridge skills, installed preset augmentations, lifecycle hooks, structural workflow overlay, Spec Kit environment, and SpecDD lint result without changing repository state.

`dev-scripts.include` runs this mode so the next programming iteration receives bootstrap failures directly.

For workflow-specific inspection:

    specify workflow overlay list speckit
    specify workflow resolve speckit

The resolved workflow should place SpecDD context after `plan`, task validation after `tasks`, authorization before `implement`, and verification after `implement`.

## Generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Spec Kit materializes executable Codex skills under `.agents/skills/`, keeps extension and preset bookkeeping under `.specify/`, and copies project workflow overlays under `.specify/workflows/overlays/`. Treat those outputs as generated integration state. Change canonical source and rerun bootstrap rather than hand-editing materialized files.

SpecDD local operator preferences remain in `.specdd/bootstrap.local.md` and are intentionally excluded from shared iteration context.

## Baseline review

After bootstrap or a deliberate integration migration:

    git status --short
    bash scripts/bootstrap.sh --check

Review generated `.specify/`, `.agents/skills/`, and `.specdd/` state according to the repository's tracking policy. Keep canonical bridge changes in `integration/` and do not maintain hand-edited copies of bridge behavior in generated command or workflow state.
