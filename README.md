# Spec Kit × SpecDD Bridge

This repository is an integration lab for using GitHub Spec Kit and SpecDD together without merging, forking, or duplicating either system.

Spec Kit owns the lifecycle of a change: feature specification, planning, task generation, implementation, and convergence. SpecDD owns the persistent model of the system: hierarchical specifications, ownership, modification authority, dependencies, local contracts, and architectural constraints.

The bridge projects current SpecDD authority into each Spec Kit feature so feature work can be planned and implemented inside the system contracts that already exist.

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
| Spec Kit | `1.0.10` |
| Spec Kit integration | `codex` |
| Stable upstream SpecDD CLI baseline | `1.1.1` |
| Temporary resolver provider | `specdd` package `1.2.0` from `dmos62/specdd-cli` branch `feature/resolve-intended-targets` |
| SpecDD framework | `1.5` |

The stable compatibility baseline was re-checked on 2026-09-23.

Upstream SpecDD CLI `1.1.1` does not expose the typed `--file`, `--folder`, and `--sdd-file` resolver transport required for pre-creation target resolution. Development bootstrap therefore installs the temporary provider package reporting `1.2.0`. Bridge runtime behavior detects the resolver capability itself rather than treating package version `1.2.0` as the semantic contract.

The temporary provider can be removed when a stable upstream SpecDD CLI exposes equivalent intended-target behavior and passes the focused parity and authority tests.

## Development install

From a bridge checkout:

    bash scripts/bootstrap.sh

Then verify without intentionally changing repository state:

    bash scripts/bootstrap.sh --check

Bootstrap pins the tested development toolchain and delegates bridge materialization to the same thin installer used by the packaging tests:

    bash scripts/install.sh --source .

Development procedures are in [docs/development.md](docs/development.md).

## Distribution model

Spec Kit `1.0.10` can install extensions and presets from remote archives and can install complete workflow packages from remote archives. Project workflow overlays are different: `workflow overlay add` accepts a local overlay file, and bundles do not package project overlays as a component.

The bridge therefore does not use a native bundle as its current distribution unit. The selected P2 model is one thin installer that obtains one immutable bridge archive, then delegates installation to the native extension, preset, integration, and workflow-overlay commands.

The installer accepts a local checkout or archive for development and an immutable GitHub tag, 40-character commit, or release archive URL for consumer packaging tests:

    bash scripts/install.sh --source .

For an immutable remote release, run the installer script from the same immutable release and pass its archive URL. Until the repository owner and release location are finalized, the command shape is:

    curl -fsSL "https://raw.githubusercontent.com/<owner>/speckit-boundary/<tag>/scripts/install.sh" |
      bash -s -- --source "https://github.com/<owner>/speckit-boundary/archive/refs/tags/<tag>.tar.gz"

Mutable branch archives such as `refs/heads/main` are rejected.

Installed state can be checked or removed through the same script:

    bash scripts/install.sh --check
    bash scripts/install.sh --remove

Spec Kit `1.0.10` does not preserve one sufficient immutable source identity for this composition: extracted extension and preset installs are recorded as local component state, while the project overlay is copied separately. A downstream repository therefore needs one small committed source/version pin for reproducibility. Defining that committed pin and the complete fresh-clone experience remains part of the downstream-user work.

The installed extension carries the bridge runtime scripts and Change Boundary schema under generated Spec Kit extension state. Materialized commands and structural workflow gates invoke that installed runtime, so a downstream repository does not need `integration/specdd/`, `integration/specdd-preset/`, or this repository's development bootstrap for normal lifecycle execution after installation.

The immutable-archive packaging path is exercised in an isolated consumer repository after the archive source is removed, including context refresh, task validation, authorization, an implementation write, and verification. Remaining downstream work is the reproducible committed source/version pin, upgrade flow, removal/reinstall semantics, fresh-clone reconstruction, and user-facing setup documentation.

## Canonical source and generated state

Canonical bridge source lives under:

    integration/specdd/
    integration/specdd-preset/

Generated Spec Kit integration state lives under locations such as:

    .agents/skills/
    .specify/

Installed runtime under `.specify/extensions/specdd/` is generated integration state even though commands and structural gates execute from it.

Do not hand-edit generated integration state. Root `.specdd/` framework state is also not an ordinary bridge implementation surface.

## Change Boundary and authorization evidence

A feature Change Boundary is refreshable planning/task context:

    specs/001-google-login/.specdd/boundary.json

It records ordinary implementation targets, primary owners, governing specs, authority domains, cross-boundary status, unresolved diagnostics, and deterministic tool-version metadata. It does not copy `Can modify` rules.

Each refresh also records fingerprint-bound effective SpecDD context under current-worktree Git metadata. The per-target SHA-256 identities are derived from normalized resolver-returned governing spec sections, including inherited and explicit-reference context. Rule text is not duplicated in the boundary or fingerprint metadata.

Authorization fresh-resolves those targets and rejects governing-contract drift before implementation. A changed `Must`, `Forbids`, `References`, referenced contract, governing chain, or resolver generation identity therefore makes the candidate boundary stale even when primary ownership is unchanged.

An unmarked multi-owner task remains coordinated across its owning domains. When one task intentionally performs all writes under one authority, task text uses `SPECDD_AUTHORITY:` and validation fresh-resolves non-owning `Can modify` permission while preserving each target's original owner.

Resolver capability determines pre-creation behavior. When complete typed intended-target support is unavailable, missing intended implementation paths remain `INTENDED_TARGET_UNSUPPORTED` rather than receiving locally inferred authority.

Successful authorization stores three operation-evidence documents in current-worktree Git metadata:

    <git-dir>/specdd/authorization-boundary.json
    <git-dir>/specdd/authorization-spec-evolution.json
    <git-dir>/specdd/authorization-git-baseline.json

The first is the exact validated Change Boundary. The fingerprint-bound companion document records exact `.sdd` evolution targets plus editable bootstrap overrides selected before implementation. The Git baseline records authorization-time `HEAD` and content/deletion identities for every dirty path.

Verification excludes unchanged dirty state that already existed when authorization succeeded. If a pre-existing dirty path changes after authorization, or a clean path becomes dirty, it remains in operation scope. Post-authorization concurrent work is therefore verified rather than guessed away. A changed Git `HEAD` requires fresh authorization because the baseline can no longer be compared safely.

Refresh-time context fingerprints are not authorization evidence and may be replaced by later context refreshes. Refreshing the feature boundary, its context fingerprints, or later editing `tasks.md` does not change existing operation evidence.

Detailed boundary, baseline, and lifecycle semantics are in [docs/change-boundary.md](docs/change-boundary.md).

## Bootstrap controls

Root SpecDD bootstrap files follow separate control rules rather than Change Boundary ownership:

- `.specdd/bootstrap.md` is immutable.
- `.specdd/bootstrap.project.md` may change only after explicit workflow or Operator selection is recorded by authorization.
- `.specdd/bootstrap.local.md` remains local/generated preference state.
- unrelated root `.specdd/` state is not implicitly editable.

Verification blocks immutable, unrelated, and unplanned shared control changes. A deliberately selected project override is reported separately from implementation writes.

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
| context | Refresh current ordinary implementation scope and effective SpecDD context identity. |
| validate | Check task ownership and applicable modification permission. |
| authorize | Recheck governing context and record immutable boundary, selection, and Git-baseline evidence. |
| implement | Change project artifacts only within the authorized operation. |
| verify | Compare post-baseline Git state with historical evidence and fresh SpecDD resolution. |

Typical direct invocations are:

    /speckit.specdd.context
    /speckit.specdd.validate tasks
    /speckit.specdd.authorize
    /speckit.specdd.verify

## Cross-domain work

One feature may legitimately span several SpecDD owner domains.

The fixture contains independent Auth and Users domains. Auth owns its service, Users owns its identity contract and repository, and Auth has explicit `Can modify` permission only for the Users-facing identity contract.

A `MULTI_AUTHORITY_TASK` warning describes ownership shape, not invalidity. A declared operation authority makes non-owning permission deterministic through `operationAuthorities` and `modificationPermissions`.

## Specification evolution

Some features require durable system-contract evolution. The bridge distinguishes ordinary implementation from `SPEC_EVOLUTION_REQUIRED` and `AUTHORITY_EVOLUTION_REQUIRED`.

When dependent implementation requires `.sdd` evolution:

1. complete specification work separately;
2. end the old authority context when authority changed;
3. refresh context and its governing-context identity;
4. authorize again, capturing a new Git baseline;
5. begin dependent implementation under new evidence.

Changed `.sdd`, bootstrap-control, Change Boundary, context-fingerprint, or Git-baseline state never retroactively authorizes implementation already performed.

## Diagnostics

| Diagnostic | Meaning |
| --- | --- |
| `INVALID_TARGET` | Input cannot identify a valid repository target. |
| `UNRESOLVED_TARGET` | A target lacks trustworthy current authority projection. |
| `INTENDED_TARGET_UNSUPPORTED` | The active resolver lacks complete typed intended-target transport. |
| `RESOLUTION_FAILED` | SpecDD resolution failed or returned unusable output. |
| `AMBIGUOUS_AUTHORITY` | Multiple resolved specifications claim ownership. |
| `MULTI_AUTHORITY_TASK` | One task contains targets owned by several authority domains. |
| `STALE_BOUNDARY` | Current scope or effective governing SpecDD context disagrees with refresh-time state. |
| `AUTHORITY_VIOLATION` | Proposed or actual implementation has invalid authority. |
| `SPECDD_DRIFT` | An actual target was not authorized though its authority domain was. |
| `SPECDD_VIOLATION` | Resulting repository state fails deterministic SpecDD checks. |
| `SPEC_EVOLUTION_PRESENT` | Changed `.sdd` files were selected at authorization. |
| `UNPLANNED_SPEC_EVOLUTION` | Changed `.sdd` files were not selected at authorization. |
| `CONTROL_STATE_CHANGED` | A selected project bootstrap override changed. |
| `CONTROL_STATE_VIOLATION` | Immutable, unrelated, or unplanned root SpecDD control state changed. |

`MISSING_SPEC_EVOLUTION` remains an architectural finding rather than a path-only deterministic result.

## Project documentation

- [docs/spec.md](docs/spec.md): concise design overview with links to focused architecture, lifecycle, and v0.1 acceptance documents.
- [docs/change-boundary.md](docs/change-boundary.md): boundary, baseline, authorization, and lifecycle evidence semantics.
- [docs/development.md](docs/development.md): development environment, packaging checks, and maintenance.
- [docs/TECH-DEBT.md](docs/TECH-DEBT.md): unresolved correctness and maintainability risks.
- [docs/TODO.md](docs/TODO.md): active implementation work.
