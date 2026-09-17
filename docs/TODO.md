# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Current baseline

The manual context → validate → implement → verify vertical slice is present.

Compatibility remains pinned to Node.js 22+, Spec Kit `1.0.7`, SpecDD CLI `1.1.1`, and SpecDD framework `1.5`. Do not silently advance these pins during v0.1.

Change Boundary v1 is defined by `integration/specdd/schemas/change-boundary.schema.json`. The adapter uses the real SpecDD resolver, derives authority only from resolved `Owns` entries, keeps derived state deterministic, and normalizes invalid targets, resolver failures, malformed output, and ownership ambiguity into structured unresolved diagnostics.

The bridge commands provide context generation, task validation, implementation authorization, and actual-change verification. Deliberate `.sdd` evolution remains separate from implementation authority and the authority-snapshot invariant remains enforced.

Phase 9 preset composition is implemented at `integration/specdd-preset/`. The pinned Spec Kit `1.0.7` preset contract stores command overrides in `provides.templates` with `type: "command"` and supports append composition.

Pinned Spec Kit `1.0.7` deliberately excludes the `generic` integration from command registration. The supported local strategy is the registrar-backed `codex` integration, which materializes Spec Kit and extension commands under `.agents/skills`. Repository bootstrap selects or switches to Codex through supported Spec Kit commands and installs the local bridge extension and preset from canonical source.

The repository generated state has been migrated successfully to the Codex integration. `bash scripts/bootstrap.sh --check` confirms the active integration, extension, preset, four bridge skills, mandatory hooks, pinned tools, and SpecDD lint state.

The isolated Codex preset smoke compares semantic upstream skill bodies after preset removal. Spec Kit `1.0.7` may reserialize YAML frontmatter and add a registrar-generated `# Speckit ... Skill` heading while restoring a core skill; those serializer-only differences are ignored while the original command body and absence of the SpecDD augmentation remain required.

The extension retains mandatory lifecycle hooks for agent-facing context, validation, authorization, and verification when commands are used directly. Hook dispatch remains agent-mediated and is not the structural enforcement boundary.

The structural workflow overlay is implemented at `integration/specdd/workflow-overlay.yml` and is installed through `specify workflow overlay add`. It adds deterministic shell steps after planning, after task generation, before implementation, and after implementation. The task gate refreshes the Change Boundary from exact task targets before validation; authorization reuses that snapshot without refresh; verification compares actual Git writes with the same planned snapshot and fresh resulting authority.

`integration/specdd/scripts/workflow_gate.py` resolves the active Spec Kit feature and delegates to the existing boundary, validation, and verification mechanics. Validation and verification CLIs support failure thresholds so deterministic `error` or `blocking` findings return nonzero status when invoked as workflow gates. The overlay does not set `continue_on_error`, so failures halt workflow execution structurally.

Phase 10 deliberate spec-evolution handling remains implemented without adding another source of truth. Evolution tasks use ordinary task-text prefixes `SPEC_EVOLUTION_REQUIRED:` and `AUTHORITY_EVOLUTION_REQUIRED:`; validation requires `.sdd`-only evolution scope and records whether fresh Change Boundary resolution is required.

Pinned Spec Kit `1.0.7` supports project workflow overlays with `id`, `extends`, optional priority and enabled state, and step edits using `insert_before`, `insert_after`, `replace`, or `remove`. Project overlays are installed through `specify workflow overlay add` rather than by editing `.specify/workflows/` directly. Workflow step failure halts execution unless `continue_on_error: true` is explicitly configured.

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
- [ ] Document the supported Codex active integration and the pinned Spec Kit `1.0.7` generic command-registration limitation.
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

Start Phase 13 with the real-CLI and semantic acceptance matrix.

- [ ] Add real-CLI cases for unresolved targets, malformed or invalid specs, multiple authority domains, and resolver execution failures.
- [ ] Map semantic scenarios A-E from `docs/spec.md` to existing fixture tests and add only missing acceptance coverage.
- [ ] Keep deterministic mechanism tests distinct from agentic architectural-classification procedures.
- [ ] Add focused regression coverage for any integration defect exposed while expanding the matrix.
- [ ] Preserve the pinned toolchain and structural workflow gates while extending coverage.

## 20. Definition of done for v0.1

- [ ] Spec Kit core is unmodified.
- [ ] SpecDD core is unmodified.
- [x] The bridge installs locally as a Spec Kit extension.
- [x] Installed bridge commands are invokable through the supported Codex active integration.
- [x] The bridge uses the real SpecDD resolver.
- [x] `speckit.specdd.context` generates a valid, rebuildable Change Boundary through its adapter.
- [x] `speckit.specdd.validate` recognizes authority and system-evolution issues.
- [x] `speckit.specdd.authorize` blocks unsafe implementation scope before implementation.
- [x] `speckit.specdd.verify` checks actual implementation scope.
- [x] Mandatory lifecycle hooks are materialized through the supported active integration.
- [x] The preset supplies SpecDD context during planning and task generation through the supported active integration without copying upstream commands.
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
