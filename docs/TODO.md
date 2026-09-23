# Implementation TODO

The bridge currently targets Spec Kit `1.0.7`, a fork-backed SpecDD CLI reporting `1.2.0`, and SpecDD framework `1.5`.

That toolchain is no longer an acceptable long-term compatibility baseline. As of 2026-09-23, the latest stable upstream
Spec Kit release is `1.0.10`, the latest stable SpecDD framework release is `1.5`, and the latest stable upstream SpecDD
CLI release is `1.1.1`. The current fork-backed CLI is therefore a project-specific capability dependency rather than a
stable upstream release.

The project should target the newest stable upstream Spec Kit and SpecDD releases available when compatibility work is
performed. Exact version pins remain appropriate for reproducibility, but they should represent the current tested stable
baseline rather than indefinitely preserving historical versions.

The repository layout also still reflects bridge development rather than downstream consumption: consumer repositories
are expected to carry canonical extension, preset, workflow-overlay, and bootstrap source. The architectural goal is a
remotely installable, self-contained integration whose generated installation state can be discarded and reproduced
without vendoring bridge source.

Use `boundary` as the implementation-independent component family.

Target public vocabulary:

- Product/display name: `Spec Kit Boundary`.
- Repository or distribution identity: `speckit-boundary`.
- Extension ID: `boundary`.
- Preset ID: `boundary-workflow`.
- Workflow overlay ID: `boundary-gates`.
- Bundle ID, when supported: `boundary`.
- User-facing commands: `speckit.boundary.*`.
- Generated feature state may continue using the term Change Boundary and `boundary.json`.
- SpecDD is the initial persistent-contract provider and implementation dependency, not the identity of the bridge.

## P1 — Move to the newest stable upstream toolchain

- [ ] Replace historical and fork-specific compatibility assumptions with the newest stable upstream Spec Kit and SpecDD
  versions while preserving required bridge behavior.
  - Treat "latest" as the newest non-prerelease upstream release available when this task is implemented, not merely the
    versions recorded in this TODO.
  - Start from the currently observed stable releases: Spec Kit `1.0.10`, SpecDD framework `1.5`, and upstream SpecDD
    CLI `1.1.1`.
  - Re-check official release metadata immediately before changing pins because these versions may have advanced.
  - Upgrade Spec Kit from `1.0.7` to the then-current stable release before designing packaging around old CLI behavior.
  - Verify extension, preset, bundle, workflow, integration, and remote-install behavior against that stable Spec Kit
    release.
  - Keep exact tested version pins in manifests and reproducible development checks after selecting the current stable
    baseline.
  - Replace the fork-backed SpecDD CLI with the newest stable upstream CLI when upstream behavior can satisfy the bridge
    contract.
  - Determine whether current upstream SpecDD resolution can resolve intended ordinary files, directories, and `.sdd`
    targets with semantics equivalent to the bridge's required typed intended-target behavior.
  - Do not preserve a fork-specific `1.2.0` version comparison as part of the durable bridge contract.
  - If the newest stable upstream SpecDD CLI still lacks a required resolver capability, isolate that fact as an explicit
    temporary provider compatibility gap rather than describing the fork as the stable SpecDD baseline.
  - In that case, document the smallest temporary compatibility mechanism and its removal condition, and continue
    targeting the latest stable SpecDD framework independently.
  - Prefer upstream-supported APIs and command behavior over fork-only behavior whenever both can satisfy the contract.
  - Add focused compatibility tests that identify supported behavior by capability and observable semantics rather than
    by historical version numbers where possible.
  - Update bootstrap, manifests, specs, documentation, fixtures, and version diagnostics consistently.
  - Ensure development checks fail clearly when an installed tool is older than or incompatible with the selected stable
    baseline.
  - Do not automatically float production installs to an untested future release; "target newest stable" means regularly
    select, test, and pin the latest stable version.

Done when:
  The repository's compatibility pins represent the newest stable upstream versions tested at implementation time,
  fork-specific version assumptions are removed from the durable architecture, and any remaining non-upstream SpecDD
  dependency is explicitly isolated as temporary capability debt.

## P2 — Establish the install and distribution model

- [ ] Determine the smallest supported packaging and installation model that lets downstream users consume one immutable
  `speckit-boundary` version without vendoring bridge source.
  - Perform this work against the stable Spec Kit baseline established by P1 rather than preserving assumptions from
    Spec Kit `1.0.7`.
  - Add focused executable coverage for local extension installation.
  - Add focused executable coverage for local preset installation.
  - Determine whether extensions can install from an immutable GitHub tag, commit, archive, or equivalent remote source.
  - Determine whether presets can install from the same immutable remote source model.
  - Determine whether the selected stable Spec Kit has a bundle primitive capable of packaging the extension, preset,
    and workflow integration as one versioned unit.
  - Determine whether workflow overlays or their current replacement can install remotely or require a local file.
  - Determine what source/version metadata Spec Kit persists and whether a separate committed downstream pin is needed.
  - Verify clean removal, reinstall, and active-integration switching behavior with Codex.
  - Prefer native Spec Kit lifecycle commands over custom installation machinery.
  - If native bundles are sufficient, use `boundary` as the single user-facing bundle.
  - Otherwise define one thin installer that downloads an immutable version and composes the native extension, preset,
    and workflow installation commands.
  - Do not require npm, PyPI, or public Spec Kit catalog publication.
  - Do not use mutable branches such as `main` as normal downstream installation identity.
  - Keep the installation model compatible with deliberate future stable-version upgrades without embedding one old
    Spec Kit repository layout into downstream projects.

Done when:
  The project has an executable, tested decision for local development installation and immutable GitHub-backed consumer
  installation, including the exact handling required for workflow integration.

## P3 — Make the installed integration self-contained

- [ ] Remove the assumption that canonical bridge source exists inside a downstream repository.
  - A downstream repository must not require `integration/specdd/`, `integration/specdd-preset/`, or this repository's
    `scripts/bootstrap.sh`.
  - Runtime commands must execute from installed integration assets or another supported installation location.
  - Remove workflow and command assumptions equivalent to `integration/specdd/scripts/...`.
  - The extension or bundle must carry or reliably locate every runtime script required by commands and structural gates.
  - The preset must compose with installed Spec Kit commands without requiring canonical preset source in the downstream
    repository.
  - Workflow gates must invoke the installed runtime through a stable installed entry point.
  - Generated Codex skills remain materializations of installed integration state rather than canonical bridge source.
  - Add an isolated downstream consumer fixture containing project contracts but no vendored bridge source.
  - Prove context, task validation, authorization, implementation gating, and verification can operate in that fixture.
  - Prove installed operation still works when canonical bridge-development paths are absent from the consumer repository.
  - Preserve current provider capability, authority, freshness, and authorization-snapshot behavior during the packaging
    change.
  - Avoid coupling runtime asset discovery to incidental filesystem details of one Spec Kit release when a supported
    installed-component mechanism exists.

Done when:
  A consumer fixture with no canonical bridge implementation source can run the complete structural lifecycle using only
  installed `speckit-boundary` state.

## P4 — Rename the public integration and isolate the SpecDD provider

- [ ] Replace `specdd` as the bridge's public identity with the implementation-independent `boundary` family while
  retaining SpecDD terminology only where it genuinely identifies the current provider.
  - Rename the extension identity to `boundary`.
  - Rename the preset identity to `boundary-workflow`.
  - Rename the workflow overlay or corresponding workflow component identity to `boundary-gates`.
  - Rename public commands to `speckit.boundary.*`.
  - Rename generated skill identities consistently.
  - Rename canonical source directories to an implementation-independent layout such as `integration/boundary/`,
    `integration/boundary-preset/`, and an appropriate workflow source location.
  - Update manifests, bootstrap/install/check behavior, tests, docs, and packaging assertions consistently.
  - Update Git metadata namespaces when doing so does not destroy required compatibility.
  - Avoid compatibility aliases unless a deliberate downstream migration requires them.
  - Keep Change Boundary terminology and `boundary.json`.
  - Separate provider-neutral bridge concepts from SpecDD-specific invocation code where current modules mix them.
  - Provider-neutral concepts include target ownership projection, non-owning modification permission, effective-context
    identity, authorization evidence, lifecycle integration, and actual-write verification.
  - SpecDD-specific code should own resolver invocation, resolver-output translation, SpecDD CLI/framework identity, and
    SpecDD capability detection.
  - Express provider compatibility primarily through required capabilities and tested semantics so later stable SpecDD
    upgrades do not require product-level renaming or architectural changes.
  - Do not build a generalized provider-plugin framework unless the separation directly simplifies the present code.

Done when:
  Public installation, command, workflow, generated-state, and documentation identities use `boundary`, while `specdd`
  remains only where it denotes the current provider or its contracts.

## P5 — Define and verify the downstream user experience

- [ ] Replace the development-repository bootstrap model with a reproducible consumer setup, upgrade, removal, and
  fresh-clone workflow.
  - A normal downstream repository should contain its own provider bootstrap/contracts, its own project `.sdd` files
    while SpecDD is active, normal Spec Kit feature artifacts, and only the minimum committed integration pin needed for
    reproducibility.
  - Installed extension, preset, workflow, generated command/skill, cache, Change Boundary, context-evidence, and other
    derived bridge state must remain non-canonical and recreatable.
  - `.specdd/bootstrap.md` remains committed project contract state while SpecDD is the active provider.
  - `.specdd/bootstrap.local.md` remains local/operator state.
  - One user-facing install operation should materialize all required extension, preset, workflow, and Codex state.
  - A fresh clone plus committed project state and the immutable external version/source must reproduce the integration.
  - Stable upstream Spec Kit and SpecDD upgrades must be deliberate operations that update the tested project pin rather
    than silently changing every downstream installation.
  - Health checks should report when newer stable upstream versions are available without silently changing the validated
    compatibility baseline.
  - Add tests for local developer installation from a checkout.
  - Add tests for consumer installation from an immutable controlled source representation.
  - Add tests proving a clean consumer repository contains no canonical bridge source after installation.
  - Add tests for clean removal and equivalent reinstall.
  - Add tests for fresh-clone reproduction.
  - Add tests that Codex materializations are recreated through supported Spec Kit mechanisms.
  - Update ignore rules so installed/generated integration state is not treated as canonical downstream source.
  - Split documentation between downstream-user setup and bridge-developer setup.
  - User documentation should cover prerequisites, install, version pinning, health checks, deliberate upgrades, removal,
    reinstall, committed files, ignored generated files, and normal Codex workflow usage.
  - Developer documentation should cover local installation, rematerialization, packaging structure, provider boundaries,
    release/tag procedure, stable dependency upgrade procedure, and consumer-fixture testing.
  - Internal extension/preset/workflow composition should not be required user knowledge when one installer or bundle can
    hide it.
  - Update bridge development checks to exercise the same packaged integration users receive rather than a special
    vendored downstream layout.
  - Remove obsolete source-layout compatibility code, tests, and documentation after the packaged consumer path is
    established.
  - Run full bootstrap, lint, boundary, validation, workflow, preset, and verification suites.

Done when:
  A downstream user can initialize a Codex project, install one immutable `speckit-boundary` version, run a health check,
  use the normal lifecycle, remove/reinstall generated state, and reproduce the same setup from a fresh clone without
  carrying bridge implementation source.

## P6 — Define ownership semantics beneath not-yet-created directories

- [ ] Resolve whether an exact owned path such as `Owns: ./future-domain` can authorize intended descendants before that
  directory exists.
  - Determine the current stable SpecDD framework and resolver contract before changing bridge ownership matching.
  - Re-evaluate this behavior after P1 because upstream resolver semantics may differ from the current fork.
  - Do not infer directory intent locally from `.sdd` text or filesystem absence; the bridge must continue to consume
    resolver semantics rather than implement a parallel SpecDD parser.
  - If resolver output can distinguish the ownership shape unambiguously, project that information through the existing
    ownership calculation.
  - If the contract remains ambiguous, keep the result conservative and document that an exact missing ownership path
    cannot act as directory ownership until its type is knowable.
  - Add focused coverage for existing owned directories, missing owned directories, exact intended files, glob-owned
    intended files, and intended-versus-created resolution parity.
