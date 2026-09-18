# Development Setup

This repository is an integration lab for Spec Kit and SpecDD. Keep upstream-generated state separate from bridge
source and keep the toolchain pinned while v0.1 semantics are being proven.

## Compatibility baseline

Selected on 2026-09-17:

| Component | v0.1 requirement | Direct evidence |
| --- | --- | --- |
| Node.js | 22+ | Runtime prerequisite; bootstrap reports the exact Node version used by each check run. |
| uv | installed | Required by supported Spec Kit and bridge command paths; no version range is claimed. |
| Spec Kit | `1.0.7` | Bootstrap, installation, preset composition, workflow overlay, and tests pass at this exact version. |
| Spec Kit integration | `codex` | Registrar-backed integration exercised by installation smoke tests and bootstrap. |
| SpecDD CLI | `1.1.1` | Resolver fixtures, validation, verification, lint, bootstrap, and install tests pass at this version. |
| SpecDD framework | `1.5` | Repository and fixture specs lint cleanly at this exact framework version. |

The compatibility range is intentionally a singleton for Spec Kit, SpecDD CLI, and the SpecDD framework.

The 2026-09-17 evidence host was Windows 10 `10.0.19045` on AMD64, and Spec Kit reported Python `3.12.11`. Those values
describe the exercised host, not a supported range. Other operating systems, architectures, Python versions, and exact
Node versions remain unverified until the repository checks run there.

Pinned Spec Kit `1.0.7` deliberately excludes the `generic` integration from its command registrar. The repository uses
the Codex integration instead of patching generated generic command files.

Upstream references:

- Spec Kit releases: https://github.com/github/spec-kit/releases
- Spec Kit installation: https://github.com/github/spec-kit/blob/main/docs/installation.md
- Spec Kit integrations: https://github.com/github/spec-kit/blob/main/docs/reference/integrations.md
- SpecDD CLI: https://github.com/specdd/cli
- SpecDD framework releases: https://github.com/specdd/specdd/releases

Do not silently advance these pins during v0.1.

## Path handling evidence

The selected Windows evidence host exercises these behaviors through the repository test suite:

- repository-relative `/` and `\` separators normalize to `/`;
- drive-qualified absolute paths are accepted only inside the selected repository root;
- foreign absolute path styles are rejected;
- backticked task paths preserve spaces and literal `[`/`]` and `{`/`}` grouping characters;
- wildcard `*` and `?` patterns remain invalid as exact task targets;
- Git porcelain `-z --no-renames` preserves special filenames before repository normalization;
- SpecDD resolver paths use the same host-style absolute-path checks.

These checks establish behavior only on hosts where they actually run.

## Prerequisites

Install Git, Node.js 22+, npm, uv, and the Codex CLI.

With nvm:

    nvm install
    nvm use

The active Spec Kit integration requires `codex` on `PATH`. Bootstrap fails explicitly when it is absent.

## Bootstrap

From the repository root:

    bash scripts/bootstrap.sh

Bootstrap:

- verifies Git, Node.js, npm, uv, and Codex;
- installs Spec Kit `1.0.7` with `uv tool`;
- installs SpecDD CLI `1.1.1` with npm;
- initializes or switches Spec Kit to the Codex integration;
- initializes SpecDD framework `1.5`;
- installs the local extension and preset in development mode;
- installs the structural workflow overlay;
- verifies materialized bridge commands, hooks, preset composition, and workflow gates;
- runs the Spec Kit environment check and `specdd lint`.

Bootstrap refuses to rewrite an existing SpecDD bootstrap whose framework version differs from `1.5`.

Integration switching and bridge installation use supported Spec Kit commands. Do not manually patch `.specify/`,
`.agents/skills/`, `.specify-agent/commands/`, or root `.specdd/` framework state.

## Rematerialize bridge source

When only canonical bridge source changed, reinstall through Spec Kit:

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

Under pinned Spec Kit `1.0.7`, do not switch to `generic` for bridge execution.

## Structural workflow enforcement

Canonical workflow-overlay source is:

    integration/specdd/workflow-overlay.yml

The installed copy under `.specify/workflows/overlays/` is generated state.

The resolved `speckit` workflow adds four deterministic shell steps:

- `specdd-context` refreshes advisory feature Change Boundary context after planning.
- `specdd-task-validation` refreshes the boundary from exact task targets and fails on deterministic error or blocking
  diagnostics.
- `specdd-authorize` validates the existing boundary without refreshing it. On success it stores the exact validated
  boundary plus the explicit `.sdd` evolution target list in current-worktree Git metadata.
- `specdd-verify` leaves feature context and authorization evidence unchanged, resolves actual implementation writes
  freshly, compares them with the authorization boundary, and rejects unplanned `.sdd` changes.

The authorization boundary and companion specification-evolution plan are outside the worktree. They are generated
historical evidence, not project source, and neither grants authority beyond the validated SpecDD context.

A later Change Boundary refresh or task edit cannot change authority or planned specification scope for an implementation
operation already in progress. Dependent implementation after deliberate specification evolution requires a new context
refresh and a new successful authorization.

Structural shell steps omit `continue_on_error`, so nonzero status propagates through the workflow engine.

Extension lifecycle hooks remain useful for direct command execution and agent-facing interpretation. They are not the
structural enforcement mechanism.

## Verify without changing canonical source

For subsequent iterations:

    bash scripts/bootstrap.sh --check

Check mode reports exact runtime versions, verifies pinned tools, active Codex integration, materialized bridge skills,
preset augmentations, lifecycle hooks, structural workflow overlay, Spec Kit environment, and SpecDD lint without
intentionally changing repository state.

For workflow inspection:

    specify workflow overlay list speckit
    specify workflow resolve speckit

The resolved workflow should place SpecDD context after `plan`, task validation after `tasks`, authorization before
`implement`, and verification after `implement`.

If check mode reports that `specdd-bridge` is not installed, run `bash scripts/bootstrap.sh` once.

## Generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Spec Kit materializes installed commands and bookkeeping under `.agents/skills/` and `.specify/`. Treat those outputs as
generated integration state.

Feature Change Boundaries are generated feature state. Authorization boundary snapshots and specification-evolution
plans are generated worktree Git metadata. None is canonical bridge source.

Some generated files may exist in repository history as baseline integration state. Acceptance checks should validate
their installed behavior while protecting canonical source from unintended changes.

SpecDD local operator preferences remain in `.specdd/bootstrap.local.md` and are excluded from shared iteration context.

## Baseline review

After bootstrap or deliberate integration migration:

    git status --short
    bash scripts/bootstrap.sh --check

Review generated `.specify/`, `.agents/skills/`, feature `.specdd/`, and root `.specdd/` state according to repository
policy. Keep canonical bridge changes under `integration/`.

The clean-clone acceptance gate also checks the full tests, fixture lint, patch integrity, unexpected canonical-source
changes, and tracked files accidentally covered by ignore rules.
