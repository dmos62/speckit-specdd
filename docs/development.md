# Development Setup

This repository is an integration lab for Spec Kit and SpecDD. Keep upstream-generated state separate from bridge source and keep the toolchain pinned while v0.1 semantics are being proven.

## Compatibility baseline

Selected on 2026-09-23:

| Component | v0.1 requirement | Direct evidence |
| --- | --- | --- |
| Node.js | 22+ | Runtime prerequisite; bootstrap reports the exact Node version used by each check run. |
| uv | installed | Required by supported Spec Kit and bridge command paths. |
| Spec Kit | `1.0.10` | Bootstrap, installation, preset composition, workflow overlay, and tests target this exact version. |
| Spec Kit integration | `codex` | Registrar-backed integration exercised by installation smoke tests and bootstrap. |
| Stable upstream SpecDD CLI | `1.1.1` | Current stable upstream baseline and comparison point for resolver compatibility. |
| Temporary resolver provider | `specdd` package `1.2.0` | Provides typed intended-target resolver transport missing from upstream `1.1.1`. |
| SpecDD framework | `1.5` | Repository and fixture specs lint against this exact framework version. |

The compatibility range is intentionally a singleton for Spec Kit and the SpecDD framework. Upstream SpecDD CLI `1.1.1` is the stable baseline, but the active development executable temporarily comes from `https://github.com/dmos62/specdd-cli.git` branch `feature/resolve-intended-targets` and reports package version `1.2.0`.

The bridge does not infer typed intended-target support from that package version. Runtime code inspects whether `specdd resolve --help` exposes the complete `--file`, `--folder`, and `--sdd-file` capability. A resolver without the complete capability remains conservative for missing targets.

The temporary provider should be removed as soon as a stable upstream SpecDD CLI exposes equivalent typed intended ordinary-file, directory, and `.sdd` target resolution and passes the focused creation-parity and authority tests.

## Prerequisites

Install Git, Node.js 22+, npm, uv, and the Codex CLI.

With nvm:

    nvm install
    nvm use

The active Spec Kit integration requires `codex` on `PATH`.

## Development bootstrap

From the repository root:

    bash scripts/bootstrap.sh

Bootstrap verifies prerequisites, installs Spec Kit `1.0.10`, installs the temporary typed-target SpecDD provider, activates the Codex integration, initializes SpecDD when required, delegates bridge materialization to `scripts/install.sh`, runs Spec Kit checks, and runs `specdd lint`.

Bootstrap separately reports the stable upstream SpecDD CLI baseline and the installed temporary provider. It also verifies the provider package version and required typed intended-target flags.

Bootstrap refuses to rewrite an existing SpecDD bootstrap whose framework version differs from `1.5`.

Do not manually patch `.specify/`, `.agents/skills/`, `.specify-agent/commands/`, or root `.specdd/` framework state.

## Packaging decision

Spec Kit `1.0.10` supports remote extension and preset installation and remote installation of complete workflow packages. Project workflow overlays remain local files installed with `specify workflow overlay add`.

A native bundle can compose extensions, presets, workflows, and steps, but it cannot own this project overlay. Replacing the overlay with a copied full upstream workflow would make the bridge own an unnecessary snapshot of Spec Kit's workflow and would couple distribution to one upstream workflow layout.

P2 therefore selects a thin installer rather than a native bundle. The installer consumes one bridge source and invokes the supported Spec Kit operations for:

- active integration selection;
- extension installation;
- preset installation;
- project workflow-overlay installation;
- removal and health checks.

The same installer is used for local development:

    bash scripts/install.sh --source .

It also accepts a local `.zip`, `.tar.gz`, or `.tgz` archive.

For controlled consumer packaging tests it accepts immutable GitHub tag, 40-character commit, or release archive URLs. Mutable branch archives are rejected.

The installer deliberately does not publish through npm, PyPI, or a public Spec Kit catalog.

## Immutable source and provenance

Spec Kit `1.0.10` does not persist enough provenance to reconstruct this three-part installation from installed state alone.

Extension and preset components installed from an extracted release are local component installs. The workflow overlay is separately copied into project overlay state. Neither gives a downstream clone one authoritative immutable bridge source.

The downstream model therefore needs one small committed source/version pin that identifies the immutable bridge release independently of generated Spec Kit state. Defining that pin, upgrade flow, and fresh-clone reproduction is part of the downstream-user task.

The current archive installer proves the packaging route, installation, Codex switching, removal, and reinstall behavior. It does not yet make runtime execution independent of canonical source paths: the structural workflow shell commands still reference `integration/specdd/scripts/...`. Self-contained installed runtime assets are the next packaging task.

## Rematerialize bridge source

When canonical bridge source changes, reinstall it through the selected component installer:

    bash scripts/install.sh --source .

Check only the bridge installation:

    bash scripts/install.sh --check

Then run the full repository check:

    bash scripts/bootstrap.sh --check

This replaces the previous manual extension, preset, and overlay sequence while still using those native Spec Kit operations internally.

## Structural workflow enforcement

Canonical workflow-overlay source is:

    integration/specdd/workflow-overlay.yml

The installed copy under `.specify/workflows/overlays/` is generated state.

The resolved `speckit` workflow adds four deterministic shell steps:

- `specdd-context` refreshes advisory feature Change Boundary context after planning.
- `specdd-task-validation` refreshes ordinary implementation scope from exact task targets and validates it.
- `specdd-authorize` validates the existing boundary and records immutable operation evidence.
- `specdd-verify` compares post-authorization Git state with that historical evidence.

Authorization evidence consists of the exact validated boundary, a fingerprint-bound companion plan, and a fingerprint-bound Git baseline. The companion records exact planned `.sdd` evolution targets and exact editable bootstrap overrides selected before implementation. The Git baseline records authorization-time `HEAD` plus content/deletion identities for every dirty path.

A later Change Boundary refresh or task edit cannot change this historical evidence. Verification excludes unchanged pre-authorization dirty state, but any path changed after authorization remains in operation scope. If Git `HEAD` changes, verification fails closed and requires fresh authorization. Optional feature worktrees can isolate concurrent operations but are not part of SpecDD authority semantics.

## Bootstrap control state

Root SpecDD bootstrap files are control state, not ordinary bridge implementation targets.

`.specdd/bootstrap.md` is immutable.

`.specdd/bootstrap.project.md` is shared project control state and may change only when explicitly selected by the Operator or authorized workflow before implementation. Authorization records that selection.

`.specdd/bootstrap.local.md` remains local/generated preference state. It may be explicitly selected locally but stays outside shared implementation-write verification and is excluded from iteration context.

Unrelated root `.specdd/` changes are never inferred as permitted implementation work.

## Verify without changing canonical source

For subsequent iterations:

    bash scripts/bootstrap.sh --check

For workflow inspection:

    specify workflow overlay list speckit
    specify workflow resolve speckit

The resolved workflow should place SpecDD context after `plan`, task validation after `tasks`, authorization before `implement`, and verification after `implement`.

## Generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Spec Kit materializes installed commands and bookkeeping under `.agents/skills/` and `.specify/`. Treat those outputs as generated integration state.

Feature Change Boundaries are generated feature state. Refresh-time effective-context evidence, authorization boundary snapshots, companion operation selections, and authorization-time Git baselines are generated current-worktree Git metadata.

SpecDD local operator preferences remain in `.specdd/bootstrap.local.md` and are excluded from shared iteration context.

## Baseline review

After bootstrap or deliberate integration migration:

    git status --short
    bash scripts/bootstrap.sh --check

Review generated `.specify/`, `.agents/skills/`, feature `.specdd/`, and root `.specdd/` state according to repository policy. Keep canonical bridge changes under `integration/` and installer/bootstrap changes under `scripts/`.

The clean-clone acceptance gate also checks the full tests, fixture lint, patch integrity, unexpected canonical-source changes, and tracked files accidentally covered by ignore rules.
