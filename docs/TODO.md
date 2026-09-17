# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Current baseline

The manual context → validate → implement → verify vertical slice is present.

Compatibility remains pinned to Node.js 22+, Spec Kit `1.0.7`, SpecDD CLI `1.1.1`, and SpecDD framework `1.5`. Do not silently advance these pins during v0.1.

Change Boundary v1 is defined by `integration/specdd/schemas/change-boundary.schema.json`. The adapter uses the real SpecDD resolver, derives authority only from resolved `Owns` entries, keeps derived state deterministic, and normalizes invalid targets, resolver failures, malformed output, and ownership ambiguity into structured unresolved diagnostics.

The bridge commands are implemented as follows:

- `speckit.specdd.context` builds or refreshes the active feature boundary.
- `speckit.specdd.validate` classifies Spec Kit task write sets and blocks unknown or conflicting implementation authority.
- `speckit.specdd.verify` checks actual Git writes against the planned authority snapshot, freshly resolves existing implementation targets, reports `.sdd` evolution separately, and includes `specdd lint`.

The local extension manifest at `integration/specdd/extension.yml` exposes those commands and remains compatible with Spec Kit `1.0.7` and SpecDD CLI `1.1.1`.

Phase 9 preset composition is implemented at `integration/specdd-preset/`. The pinned Spec Kit `1.0.7` preset contract stores command overrides in `provides.templates` with `type: "command"` and supports `append` composition. The bridge preset uses that strategy so upstream `speckit.plan`, `speckit.tasks`, and `speckit.converge` behavior remains intact rather than being copied.

Pinned Spec Kit `1.0.7` resolves those append layers into installed preset `.composed` command artifacts. It deliberately excludes the `generic` integration from agent command registration, however, so preset composition is not materialized into `.specify-agent/commands`. Extension command registration has the same generic-integration limitation. The installation smoke now verifies resolver composition separately from generic command materialization instead of treating unchanged generic command files as a composition failure.

The preset:

- requires the local SpecDD bridge extension `0.1.0`,
- refreshes Change Boundary context during planning and records a concise `SpecDD Impact` projection without copying persistent SpecDD constraints,
- preserves Spec Kit user-story grouping while preferring one primary authority per implementation task where practical,
- keeps normal implementation, spec evolution, and authority evolution distinct,
- runs task-stage SpecDD validation before task generation reports completion,
- incorporates `SPECDD_VIOLATION`, `SPECDD_DRIFT`, `MISSING_SPEC_EVOLUTION`, and `AUTHORITY_VIOLATION` into convergence while preserving upstream append-only behavior.

Phase 10 deliberate spec-evolution handling is implemented without adding another source of truth. Evolution tasks use ordinary task-text prefixes `SPEC_EVOLUTION_REQUIRED:` and `AUTHORITY_EVOLUTION_REQUIRED:`; validation projects those classifications into machine-readable output, requires `.sdd`-only evolution scope, and records whether a fresh Change Boundary is required and whether the prior authority context ends. Change Boundary discovery excludes `.sdd` evolution targets, and task generation places a separate context-refresh task between deliberate evolution and dependent implementation. The validation command surfaces proposed `.sdd` deltas only as advisory output and never applies them. Fixture verification covers the authority-snapshot invariant: authority changed by a specification operation remains unusable under the old boundary and becomes usable only in a subsequent operation after fresh resolution.

Preset tests cover source contracts plus isolated local Spec Kit initialization that installs the extension and preset, verifies resolver-composed command content, confirms generic command files remain unchanged under the pinned release, removes the preset, and confirms core generic commands remain intact. The command runner decodes subprocess output as UTF-8 so the smoke remains stable on Windows hosts that otherwise default to a legacy code page.

## 11. Phase 11 — Add lifecycle hooks

Pinned Spec Kit `1.0.7` exposes the required planning, task, implementation, and convergence hook events through `.specify/extensions.yml`, but mandatory hook execution is delegated to the active agent rather than enforced by the engine.

The current repository is initialized with the `generic` integration. In pinned Spec Kit `1.0.7`, `generic` is deliberately excluded from extension and preset command registration. Registering lifecycle hooks that invoke `speckit.specdd.*` now would therefore create hooks whose bridge commands normal generic usage cannot invoke.

Resolve the active-integration strategy before adding lifecycle hooks. Do not register dead hooks merely to satisfy the manifest.

### TODO

- [ ] Decide and authorize a registrar-backed active integration for local bootstrap, or define another supported path that makes extension commands invokable without patching generated `.specify-agent/commands`.
- [ ] Re-run extension and preset installation smoke tests with the selected supported invocation path.
- [ ] Add reliable post-plan context refresh.
- [ ] Add post-tasks validation.
- [ ] Add a pre-implementation blocking authority gate.
- [ ] Add post-implementation verification.
- [ ] Evaluate convergence hooks separately.
- [ ] Keep critical enforcement in workflow structure when hook dispatch alone cannot guarantee failure propagation.

Exit criteria: normal supported integration usage can invoke every registered bridge gate, and mandatory authority failures cannot be silently bypassed because of unavailable commands or agent-only dispatch.

## 12. Phase 12 — Add workflow overlay

Workflow structure is expected to carry critical deterministic gates when Phase 11 confirms that agent-dispatched hooks alone are insufficient.

### TODO

- [ ] Verify overlay syntax against the pinned Spec Kit release.
- [ ] Add deterministic context, validation, pre-implementation authority, and verification steps.
- [ ] Test step ordering and failure propagation.
- [ ] Avoid duplicating equivalent hook behavior.
- [ ] Document the final responsibility split between hooks and overlay steps.

Exit criteria: critical authority gates are structural rather than dependent only on prompt memory or hook-dispatch compliance.

## 13. Phase 13 — Complete the test matrix

### TODO

- [ ] Expand real-CLI integration coverage for unresolved paths, invalid specs, multiple domains, and CLI failures.
- [ ] Automate semantic scenarios A-E from `docs/spec.md`; reuse existing fixture coverage for local, cross-domain, unauthorized-write, explicit spec-evolution, and authority re-resolution behavior rather than duplicating it.
- [ ] Add a regression test for every integration bug found during development.

Exit criteria: deterministic checks are automated and agentic semantic cases have repeatable acceptance procedures.

## 14. Phase 14 — Documentation

### TODO

- [ ] Write the project README after the first vertical slice works.
- [ ] Document installation and local development for both the extension and preset.
- [ ] Document the supported active integration and the pinned Spec Kit `1.0.7` generic command-registration limitation.
- [ ] Document Change Boundary semantics and regeneration.
- [ ] Document bridge command usage and diagnostics.
- [ ] Document task-partition guidance and why Spec Kit tasks are not synchronized with SpecDD tasks.
- [ ] Document constitution versus root SpecDD responsibilities.
- [ ] Document the authority-snapshot invariant and spec-evolution lifecycle.
- [ ] Add a cross-domain example and troubleshooting for missing CLI or unresolved targets.

## 15. Phase 15 — v0.1 hardening

### TODO

- [ ] Pin tested Spec Kit and SpecDD compatibility ranges from actual test evidence.
- [ ] Add compatibility assertions where useful.
- [ ] Make external dependency errors explicit.
- [ ] Verify supported operating-system path handling.
- [ ] Make generated state deterministic enough for tests.
- [ ] Confirm the default policy for `boundary.json` is generated/uncommitted state unless review evidence proves otherwise.
- [ ] Confirm uninstall leaves no patched upstream files.
- [ ] Re-run all acceptance scenarios from a clean clone.
- [ ] Tag v0.1 only after clean-clone reproduction succeeds.

## 18. Deferred work

Do not implement before v0.1 proves the semantic bridge: bundle/public registry publishing, automatic `.sdd` editing or approval, CI integration, rich requirement-to-code traceability, graph/IDE visualization, automatic task rewriting, persistent integration databases, cross-repository authority, or a general bridge-policy language.

## 19. Next coding session

Resolve the pinned Spec Kit `1.0.7` generic command-registration gap before adding lifecycle hooks:

- [ ] Select a supported invocation strategy in which installed `speckit.specdd.*` commands are actually available to the active agent.
- [ ] If that requires changing repository bootstrap behavior, first identify or create the authoritative SpecDD ownership contract for the affected bootstrap artifact before editing it.
- [ ] Extend the isolated installation smoke to prove bridge command availability and preset materialization through the selected strategy.
- [ ] Only then register lifecycle hooks that reference the bridge commands.
- [ ] Keep pre-implementation authority validation blocking and move critical enforcement to workflow structure where hook dispatch is not engine-enforced.

Do not start workflow overlays or bundle packaging until bridge command availability and hook behavior against the pinned release are known.

## 20. Definition of done for v0.1

- [ ] Spec Kit core is unmodified.
- [ ] SpecDD core is unmodified.
- [x] The bridge installs locally as a Spec Kit extension.
- [ ] Installed bridge commands are invokable through the selected supported active integration.
- [x] The bridge uses the real SpecDD resolver.
- [x] `speckit.specdd.context` generates a valid, rebuildable Change Boundary through its adapter.
- [x] `speckit.specdd.validate` recognizes authority and system-evolution issues.
- [x] `speckit.specdd.verify` checks actual implementation scope.
- [ ] The preset supplies SpecDD context during planning and task generation through the selected supported active integration without copying upstream commands.
- [x] Feature user stories may span multiple SpecDD domains while implementation tasks remain authority-local where practical.
- [x] Spec Kit tasks remain the canonical feature execution tasks.
- [x] SpecDD remains the canonical persistent system model.
- [x] Unauthorized cross-domain mutation is detected.
- [x] Legitimate cross-domain work is representable.
- [x] Spec evolution is distinct from implementation conflict.
- [x] Authority evolution requires re-resolution before new rights can be used.
- [ ] Required semantic acceptance tests pass.
- [ ] A clean clone reproduces the development setup from documentation.

## 21. Core implementation constraint

Spec Kit owns the change lifecycle. SpecDD owns persistent system semantics. The bridge resolves, projects, validates, and verifies; it must not become a third competing specification system.
