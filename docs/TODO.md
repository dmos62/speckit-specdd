# Implementation TODO

The tested compatibility baseline remains:

- Node.js 22+;
- Spec Kit `1.0.10`;
- Spec Kit integration `codex`;
- stable upstream SpecDD CLI `1.1.1`;
- temporary typed intended-target provider package reporting `1.2.0`;
- SpecDD framework `1.5`.

P1–P3 established resolver-capability detection, immutable authorization evidence, the thin installer, and installed-runtime operation without vendored bridge source. Their implementation history belongs in Git and the focused design/development documentation rather than in this active work list.

Work in the order below unless a newly discovered correctness issue requires reprioritization.

## P4 — Rename the public integration and isolate the SpecDD provider

The target product vocabulary is:

- product/display name: `Spec Kit Boundary`;
- repository or distribution identity: `speckit-boundary`;
- extension ID: `boundary`;
- preset ID: `boundary-workflow`;
- workflow overlay ID: `boundary-gates`;
- bundle ID, when supported: `boundary`;
- user-facing commands: `speckit.boundary.*`;
- generated feature state may continue using the term Change Boundary and `boundary.json`;
- SpecDD is the initial persistent-contract provider and implementation dependency, not the identity of the bridge.

### P4.0 — Repair the current test baseline

- [ ] Remove stale test expectations that downstream runtime failures instruct users to run this repository's development bootstrap.
  - Missing SpecDD-provider tests should assert an explicit provider/dependency failure and actionable provider repair guidance.
  - Missing Git tests should assert an explicit Git dependency failure and actionable Git installation/repair guidance.
  - Do not restore development-only `scripts/bootstrap.sh` remediation text to downstream runtime errors merely to satisfy old tests.
- [ ] Update installation/distribution tests that expect `specify workflow resolve` to print structural shell command bodies.
  - Assert workflow overlay attribution and structural step placement from resolver output.
  - Inspect installed overlay/runtime materialization when the exact runtime path itself must be tested.
  - Preserve the stronger isolated-consumer lifecycle execution test as proof that installed runtime paths actually work.
- [ ] Run the full test suite and return it to green before using it as the P4 migration signal.

Done when:
  The current SpecDD-named implementation has a green test baseline without reintroducing development-repository assumptions into downstream behavior.

### P4.1 — Replace the public `specdd` identity with `boundary`

- [ ] Rename public integration identities consistently.
  - Rename the extension identity to `boundary`.
  - Rename the preset identity to `boundary-workflow`.
  - Rename the workflow overlay identity to `boundary-gates`.
  - Rename public commands to `speckit.boundary.*`.
  - Rename generated Codex skill identities consistently.
  - Rename canonical source directories to an implementation-independent layout such as `integration/boundary/` and `integration/boundary-preset/`.
  - Update installer/bootstrap constants, checks, package assertions, workflow source, manifests, and tests.
- [ ] Rename bridge-owned generated namespaces where they currently expose the provider name.
  - Move installed runtime references from `.specify/extensions/specdd/` to the new extension identity.
  - Move feature-owned bridge state out of a provider-named namespace if doing so can be completed atomically with the migration.
  - Move bridge-owned Git metadata out of `<git-dir>/specdd/` if doing so does not require preserving an already-supported downstream compatibility contract.
  - Keep root `.specdd/` provider bootstrap and contract state provider-specific.
- [ ] Replace public operation metadata such as `SPECDD_AUTHORITY:` with provider-neutral vocabulary.
- [ ] Rename diagnostics only when the diagnostic describes a bridge concept rather than a genuine SpecDD-provider result.
  - Ownership projection, scope drift, authorization, lifecycle, and actual-write verification should be provider-neutral.
  - SpecDD CLI/framework failures and SpecDD contract/lint results may retain provider-specific terminology where that identity is meaningful.
- [ ] Avoid compatibility aliases unless an actual downstream migration requirement is identified.
- [ ] Update `.sdd` ownership/reference paths as canonical source moves.
- [ ] Keep Change Boundary terminology and `boundary.json`.

Done when:
  Public installation, command, workflow, generated-state, operation-metadata, and documentation identities use the `boundary` family while `specdd` remains only where it denotes the active provider or its contracts.

### P4.2 — Isolate the current SpecDD provider

- [ ] Separate provider-neutral bridge mechanics from SpecDD invocation where current modules mix them.
- [ ] Keep provider-neutral mechanics responsible for:
  - target ownership projection;
  - modification-permission projection;
  - effective-context identity;
  - Change Boundary construction and semantic consistency;
  - lifecycle validation;
  - authorization evidence;
  - Git operation baselines;
  - actual-write verification.
- [ ] Keep SpecDD-specific code responsible for:
  - `specdd resolve` invocation;
  - resolver-output translation;
  - `Owns` and `Can modify` interpretation from resolver-returned sections;
  - SpecDD CLI/framework identity;
  - typed intended-target capability detection;
  - SpecDD lint execution.
- [ ] Prefer one or a few focused provider modules over a generalized provider-plugin framework.
- [ ] Express provider compatibility through required capabilities and tested semantics rather than product naming or package-version assumptions.
- [ ] Preserve the rule that the bridge consumes resolver semantics instead of parsing `.sdd` source as an independent authority engine.

Done when:
  The bridge lifecycle and evidence model can be understood without SpecDD terminology, while the current SpecDD adapter remains small, explicit, and fully tested.

### P4.3 — Normalize documentation after the rename

- [ ] Keep `README.md` focused on user-facing purpose, install/use flow, generated-versus-canonical state, and links to detailed documents.
- [ ] Keep `docs/spec.md` as the concise current design overview.
- [ ] Keep `docs/spec-architecture.md` focused on provider-neutral structures and responsibility boundaries.
- [ ] Keep `docs/spec-lifecycle.md` focused on lifecycle transitions and convergence.
- [ ] Keep `docs/change-boundary.md` focused on Change Boundary derivation, freshness, semantic consistency, and its relationship to authorization.
- [ ] Consider extracting authorization snapshot, Git-baseline, concurrent-dirty-state, and control-selection semantics into a focused authorization-evidence document if `docs/change-boundary.md` remains responsible for too many independent concepts after P4.
- [ ] Consider extracting SpecDD-specific bootstrap, resolver, version, lint, `.sdd`, `Owns`, and `Can modify` details into a provider-focused document once the provider boundary exists in code.
- [ ] Make `docs/spec-v0.1.md` explicitly historical or move it under a history/archive location after checking all references and tests.
- [ ] Remove completed migration narrative from active TODO/debt documents instead of retaining them as changelogs.
- [ ] Split downstream-user setup from bridge-developer procedures where P5 introduces the final reproducible consumer workflow.
- [ ] Do not modify `docs/architecture-exploration-guidance.md`.
- [ ] Keep documentation files below 250 lines and split by responsibility rather than by arbitrary size.

Done when:
  Current docs describe one implemented architecture, historical acceptance material is clearly historical, provider details have one obvious home, and lifecycle/architecture/development documents do not duplicate each other's procedures.

### P4.4 — Complete migration coverage

- [ ] Update boundary, validation, authorization, verification, workflow, preset, packaging, and bootstrap tests for the new identities.
- [ ] Add a focused stale-public-identity check after the migration is complete.
  - Exclude explicitly historical material and provider-specific implementation references.
  - Catch obsolete public command, extension, preset, overlay, generated-skill, and canonical-source names.
- [ ] Run full bootstrap, lint, boundary, validation, workflow, preset, distribution, and verification suites.
- [ ] Review `files.include` after P4 and re-exclude migration-only tests/helpers that are no longer useful in normal implementation context.

Done when:
  The full repository passes without obsolete public SpecDD bridge identities outside deliberate provider or historical contexts.

## P5 — Define and verify the downstream user experience

- [ ] Replace the development-repository bootstrap model with a reproducible consumer setup, upgrade, removal, and fresh-clone workflow.
- [ ] Define one committed immutable `speckit-boundary` source/version pin because Spec Kit `1.0.10` installed component and overlay provenance is insufficient to reconstruct the composed installation.
- [ ] Keep downstream canonical state minimal:
  - the project's own provider bootstrap/contracts;
  - project persistent contracts while that provider is active;
  - normal Spec Kit feature artifacts;
  - the immutable Boundary source/version pin.
- [ ] Keep installed extension, preset, workflow, generated command/skill, cache, Change Boundary, context-evidence, authorization-evidence, and other derived integration state non-canonical and recreatable.
- [ ] Provide one user-facing install operation that materializes all required extension, preset, workflow, and Codex state from the committed immutable pin.
- [ ] Define deliberate upgrade behavior that updates the tested pin rather than silently changing downstream installations.
- [ ] Make health checks report newer stable upstream versions without silently changing the compatibility baseline.
- [ ] Add coverage for:
  - local developer installation from a checkout;
  - installation from an immutable controlled source representation;
  - a clean consumer repository with no canonical bridge source;
  - clean removal and equivalent reinstall;
  - fresh-clone reconstruction;
  - recreation of Codex materializations through supported Spec Kit mechanisms.
- [ ] Update ignore rules so installed/generated integration state is not treated as canonical downstream source.
- [ ] Finish the downstream-user/developer documentation split described in P4.3.
- [ ] Remove obsolete source-layout compatibility code, tests, and documentation after the packaged consumer path is established.
- [ ] Run the complete supported test/check matrix.

Done when:
  A downstream user can initialize a Codex project, install one immutable `speckit-boundary` version, run a health check, use the normal lifecycle, remove/reinstall generated state, and reproduce the same setup from a fresh clone without carrying bridge implementation source.

## P6 — Define ownership semantics beneath not-yet-created directories

- [ ] Determine whether an exact owned path such as `Owns: ./future-domain` can authorize intended descendants before that directory exists.
- [ ] Confirm the behavior against the supported stable SpecDD framework and resolver contract before changing bridge ownership matching.
- [ ] Do not infer directory intent locally from `.sdd` text or filesystem absence.
- [ ] If resolver output distinguishes the intended ownership shape unambiguously, project that information through the existing ownership calculation.
- [ ] If the provider contract remains ambiguous, keep the result conservative and document that an exact missing ownership path cannot act as directory ownership until its type is knowable.
- [ ] Add focused coverage for:
  - existing owned directories;
  - missing owned directories;
  - exact intended files;
  - glob-owned intended files;
  - intended-versus-created resolution parity.

Done when:
  Intended descendants receive authority only when the provider exposes enough information to establish that ownership without bridge-side semantic invention.
