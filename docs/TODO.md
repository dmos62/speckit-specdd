# Implementation TODO

The bridge targets Spec Kit `1.0.10`, SpecDD framework `1.5`, and stable upstream SpecDD CLI `1.1.1` as its compatibility baseline.

Compatibility migration verification completed on 2026-09-23. Development bootstrap succeeded with Spec Kit `1.0.10`, the temporary typed intended-target provider package reporting `1.2.0`, and SpecDD framework `1.5`. The focused boundary suite, including real-provider intended-target coverage, passed; preset and workflow suites passed except for a stale workflow-source assertion that still expected bootstrap to manage the overlay directly after P2 delegated that work to the installer.

Upstream SpecDD CLI `1.1.1` still documents that resolver targets must exist and does not expose the bridge's required typed intended-target transport. The development bootstrap therefore continues to install the fork-backed CLI package reporting `1.2.0` only as a temporary resolver capability provider. Bridge runtime behavior detects typed intended-target support by observable CLI capability rather than by the provider package version. Remove the temporary provider as soon as a stable upstream CLI exposes equivalent intended ordinary-file, directory, and `.sdd` target resolution and passes the focused parity tests.

Spec Kit's extension manifest can express one version constraint for the external `specdd` tool, not a separate stable-upstream baseline plus temporary capability-provider constraint. The extension therefore intentionally pins the temporary provider package at `1.2.0` while repository documentation records upstream `1.1.1` as the stable compatibility baseline.

P2 established the installation model against Spec Kit `1.0.10`. Extensions, presets, and complete workflows can use remote archive sources, but project workflow overlays are local-only and native bundles do not package overlays. The bridge therefore uses `scripts/install.sh` as a thin composition layer over native Spec Kit lifecycle commands instead of copying the upstream `speckit` workflow into a custom workflow package. The installer supports local checkout/archive installation and immutable GitHub tag, commit, or release archives, rejects mutable branch archives, and supports clean removal, reinstall, health checks, and Codex integration switching.

P3 made installed operation independent of canonical bridge source. Commands and structural workflow gates now execute the Python runtime from installed extension state, schema loading follows the bundled installed schema, and downstream runtime diagnostics no longer direct consumers to the bridge-development bootstrap. Distribution coverage uses an isolated consumer project with SpecDD contracts but no vendored bridge source and exercises context, task validation, authorization, an implementation write, and verification after immutable-archive installation.

Spec Kit `1.0.10` still does not persist one sufficient immutable source identity for that composed installation. Extracted extension and preset installs are local component state and the overlay is copied separately, so downstream reproducibility requires one small committed immutable source/version pin. P5 owns the final pin format, upgrade behavior, and fresh-clone reconstruction.

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

## P4 — Rename the public integration and isolate the SpecDD provider

- [ ] Replace `specdd` as the bridge's public identity with the implementation-independent `boundary` family while retaining SpecDD terminology only where it genuinely identifies the current provider.
  - Rename the extension identity to `boundary`.
  - Rename the preset identity to `boundary-workflow`.
  - Rename the workflow overlay or corresponding workflow component identity to `boundary-gates`.
  - Rename public commands to `speckit.boundary.*`.
  - Rename generated skill identities consistently.
  - Rename canonical source directories to an implementation-independent layout such as `integration/boundary/`, `integration/boundary-preset/`, and an appropriate workflow source location.
  - Update manifests, bootstrap/install/check behavior, tests, docs, and packaging assertions consistently.
  - Update Git metadata namespaces when doing so does not destroy required compatibility.
  - Avoid compatibility aliases unless a deliberate downstream migration requires them.
  - Keep Change Boundary terminology and `boundary.json`.
  - Separate provider-neutral bridge concepts from SpecDD-specific invocation code where current modules mix them.
  - Provider-neutral concepts include target ownership projection, non-owning modification permission, effective-context identity, authorization evidence, lifecycle integration, and actual-write verification.
  - SpecDD-specific code should own resolver invocation, resolver-output translation, SpecDD CLI/framework identity, and SpecDD capability detection.
  - Express provider compatibility primarily through required capabilities and tested semantics so later stable SpecDD upgrades do not require product-level renaming or architectural changes.
  - Do not build a generalized provider-plugin framework unless the separation directly simplifies the present code.

Done when:
  Public installation, command, workflow, generated-state, and documentation identities use `boundary`, while `specdd` remains only where it denotes the current provider or its contracts.

## P5 — Define and verify the downstream user experience

- [ ] Replace the development-repository bootstrap model with a reproducible consumer setup, upgrade, removal, and fresh-clone workflow.
  - A normal downstream repository should contain its own provider bootstrap/contracts, its own project `.sdd` files while SpecDD is active, normal Spec Kit feature artifacts, and only the minimum committed integration pin needed for reproducibility.
  - Define one committed immutable `speckit-boundary` source/version pin because installed Spec Kit `1.0.10` component and overlay provenance is insufficient to reconstruct the P2 composition.
  - Installed extension, preset, workflow, generated command/skill, cache, Change Boundary, context-evidence, and other derived bridge state must remain non-canonical and recreatable.
  - `.specdd/bootstrap.md` remains committed project contract state while SpecDD is the active provider.
  - `.specdd/bootstrap.local.md` remains local/operator state.
  - One user-facing install operation should materialize all required extension, preset, workflow, and Codex state from the committed immutable pin.
  - A fresh clone plus committed project state and the immutable external version/source must reproduce the integration.
  - Stable upstream Spec Kit and SpecDD upgrades must be deliberate operations that update the tested project pin rather than silently changing every downstream installation.
  - Health checks should report when newer stable upstream versions are available without silently changing the validated compatibility baseline.
  - Add tests for local developer installation from a checkout.
  - Add tests for consumer installation from an immutable controlled source representation.
  - Add tests proving a clean consumer repository contains no canonical bridge source after installation.
  - Add tests for clean removal and equivalent reinstall.
  - Add tests for fresh-clone reproduction.
  - Add tests that Codex materializations are recreated through supported Spec Kit mechanisms.
  - Update ignore rules so installed/generated integration state is not treated as canonical downstream source.
  - Split documentation between downstream-user setup and bridge-developer setup.
  - User documentation should cover prerequisites, install, version pinning, health checks, deliberate upgrades, removal, reinstall, committed files, ignored generated files, and normal Codex workflow usage.
  - Developer documentation should cover local installation, rematerialization, packaging structure, provider boundaries, release/tag procedure, stable dependency upgrade procedure, and consumer-fixture testing.
  - Internal extension/preset/workflow composition should not be required user knowledge when the installer hides it.
  - Update bridge development checks to exercise the same packaged integration users receive rather than a special vendored downstream layout.
  - Remove obsolete source-layout compatibility code, tests, and documentation after the packaged consumer path is established.
  - Run full bootstrap, lint, boundary, validation, workflow, preset, and verification suites.

Done when:
  A downstream user can initialize a Codex project, install one immutable `speckit-boundary` version, run a health check, use the normal lifecycle, remove/reinstall generated state, and reproduce the same setup from a fresh clone without carrying bridge implementation source.

## P6 — Define ownership semantics beneath not-yet-created directories

- [ ] Resolve whether an exact owned path such as `Owns: ./future-domain` can authorize intended descendants before that directory exists.
  - Determine the current stable SpecDD framework and resolver contract before changing bridge ownership matching.
  - Re-evaluate this behavior after P1 because upstream resolver semantics may differ from the current fork.
  - Do not infer directory intent locally from `.sdd` text or filesystem absence; the bridge must continue to consume resolver semantics rather than implement a parallel SpecDD parser.
  - If resolver output can distinguish the ownership shape unambiguously, project that information through the existing ownership calculation.
  - If the contract remains ambiguous, keep the result conservative and document that an exact missing ownership path cannot act as directory ownership until its type is knowable.
  - Add focused coverage for existing owned directories, missing owned directories, exact intended files, glob-owned intended files, and intended-versus-created resolution parity.
