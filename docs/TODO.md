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

The preset:

- requires the local SpecDD bridge extension `0.1.0`,
- refreshes Change Boundary context during planning and records a concise `SpecDD Impact` projection without copying persistent SpecDD constraints,
- preserves Spec Kit user-story grouping while preferring one primary authority per implementation task where practical,
- keeps normal implementation, spec evolution, and authority evolution distinct,
- runs task-stage SpecDD validation before task generation reports completion,
- incorporates `SPECDD_VIOLATION`, `SPECDD_DRIFT`, `MISSING_SPEC_EVOLUTION`, and `AUTHORITY_VIOLATION` into convergence while preserving upstream append-only behavior.

Preset tests cover source contracts plus an isolated local Spec Kit initialization that installs the extension and preset, verifies composed commands, removes the preset, and confirms core commands are restored. The prior worktree-mutating extension smoke is no longer needed because installation is exercised in the isolated test repository.

## 10. Phase 10 — Add deliberate spec-evolution handling

### TODO
- [ ] Represent `SPEC_EVOLUTION_REQUIRED` explicitly in durable bridge output where needed.
- [ ] Represent `AUTHORITY_EVOLUTION_REQUIRED` explicitly in durable bridge output where needed.
- [ ] Surface proposed `.sdd` deltas without applying them automatically.
- [ ] End the current authority context after an authority-changing spec edit.
- [ ] Require a fresh Change Boundary before implementation continues.
- [ ] Test a new durable Auth-to-Users contract.
- [ ] Test an intentional change to write authority.
- [ ] Verify newly proposed authority is unusable until re-resolution.

Exit criteria: legitimate architecture evolution works without allowing an operation to self-authorize.

## 11. Phase 11 — Add lifecycle hooks

Only start after context, validate, verify, and preset composition work manually.

### TODO
- [ ] Verify supported hook names and failure semantics in the pinned Spec Kit release.
- [ ] Add post-plan context refresh if reliable.
- [ ] Add post-tasks validation.
- [ ] Add a pre-implementation blocking authority gate.
- [ ] Add post-implementation verification.
- [ ] Evaluate convergence hooks separately.
- [ ] Ensure mandatory failures cannot be silently ignored.
- [ ] Move critical gates to workflow steps if hook semantics are insufficient.

Exit criteria: normal Spec Kit usage invokes bridge gates at required lifecycle transitions.

## 12. Phase 12 — Add workflow overlay

### TODO
- [ ] Verify overlay syntax against the pinned Spec Kit release.
- [ ] Add deterministic context, validation, pre-implementation authority, and verification steps.
- [ ] Test step ordering and failure propagation.
- [ ] Avoid duplicating equivalent hook behavior.
- [ ] Document the final responsibility split between hooks and overlay steps.

Exit criteria: critical authority gates are structural rather than dependent only on prompt memory.

## 13. Phase 13 — Complete the test matrix

### TODO
- [ ] Expand real-CLI integration coverage for unresolved paths, invalid specs, multiple domains, and CLI failures.
- [ ] Automate semantic scenarios A-E from `docs/spec.md`; existing fixture coverage for local, cross-domain, and unauthorized-write behavior should be reused rather than duplicated.
- [ ] Add a regression test for every integration bug found during development.

Exit criteria: deterministic checks are automated and agentic semantic cases have repeatable acceptance procedures.

## 14. Phase 14 — Documentation

### TODO
- [ ] Write the project README after the first vertical slice works.
- [ ] Document installation and local development for both the extension and preset.
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

Start Phase 10 with deliberate spec evolution:

- [ ] Define the smallest representation for `SPEC_EVOLUTION_REQUIRED` and `AUTHORITY_EVOLUTION_REQUIRED` that does not create another source of truth.
- [ ] Reuse the current authority-snapshot invariant rather than adding parallel authorization logic.
- [ ] Add fixture coverage for a durable Auth-to-Users contract before adding automatic lifecycle hooks.
- [ ] Keep `.sdd` delta generation advisory; do not apply specification changes automatically.

Do not start hooks, workflow overlays, or bundle packaging before deliberate spec-evolution handling works against the pinned releases.

## 20. Definition of done for v0.1

- [ ] Spec Kit core is unmodified.
- [ ] SpecDD core is unmodified.
- [x] The bridge installs locally as a Spec Kit extension.
- [x] The bridge uses the real SpecDD resolver.
- [x] `speckit.specdd.context` generates a valid, rebuildable Change Boundary through its adapter.
- [x] `speckit.specdd.validate` recognizes authority and system-evolution issues.
- [x] `speckit.specdd.verify` checks actual implementation scope.
- [x] The preset supplies SpecDD context during planning and task generation without copying upstream commands.
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
