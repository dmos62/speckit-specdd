# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Implementation strategy

Build the remaining integration in this order:

1. package the context command in the local Spec Kit extension,
2. implement validation and task-partition guidance,
3. implement verification from actual changed files,
4. augment Spec Kit planning, tasks, and convergence,
5. add deliberate spec-evolution handling,
6. add hooks and then a workflow overlay,
7. harden tests, documentation, and compatibility.

Do not begin bundle packaging, automatic `.sdd` editing, or workflow automation before the manual vertical slice works.

The first milestone remains: context → validate → implement → verify.

The pinned SpecDD 1.1.1 resolver contract has been inspected against the two-domain fixture. `directories` contains root-to-local resolved context, resolved specs expose repository-relative forward-slash `path` values, and section bodies contain the raw resolved entries needed by the bridge. Host-absolute `rootDirectoryPath` and `targetPath` values must not enter derived state. Because the resolver has no dedicated primary-authority field, the adapter derives authority narrowly from resolved `Owns` entries without parsing `.sdd` independently.

Change Boundary v1 uses JSON Schema Draft 2020-12 at `integration/specdd/schemas/change-boundary.schema.json`. Paths are non-empty repository-relative forward-slash paths without absolute prefixes, backslashes, duplicate separators, trailing slash, or `.`/`..` segments. Resolved spec and authority paths end in `.sdd`. `crossBoundary` is derived from distinct authorities. Unresolved entries preserve original input and optional normalized path. Generation metadata records SpecDD CLI/framework versions without a timestamp so regeneration remains deterministic.

The adapter at `integration/specdd/scripts/boundary.py` consumes compact resolver JSON, derives primary authority from resolved `Owns`, validates the checked-in schema, writes atomically, and normalizes invalid targets, resolver failures, malformed output, and authority ambiguity into structured unresolved diagnostics. Tests cover normalization, SpecDD glob semantics, authority derivation, schema validation, output modes, and the real two-domain fixture. SpecDD CLI version detection reads the installed npm package and falls back to `npm list --global`; framework version comes from the nearest `.specdd/bootstrap.md`.

The context command source at `integration/specdd/commands/context.md` resolves the active feature through Spec Kit state, prefers explicit user targets, otherwise discovers exact targets from `tasks.md` before `plan.md`, and delegates normalization, resolver, ownership, schema validation, and atomic replacement to the adapter. Intended-but-missing paths remain unresolved diagnostics. If no target is named, stale derived boundary state is removed. The command reports authorities, cross-boundary status, and unresolved diagnostics by code. The Python test suite includes fixture-backed deterministic regeneration coverage; installed command discovery remains Phase 6 work.

## 6. Phase 6 — Create the Spec Kit extension manifest

Create `integration/specdd/extension.yml`.

The current effective SpecDD authority does not cover `integration/specdd/extension.yml`: the root project spec owns selected repository artifacts but does not grant `Owns` or `Can modify` authority for this manifest path, and no nearer supplied spec owns it. Do not create the manifest by relying on authority added during the same operation. Establish the path's durable SpecDD ownership or modification authority deliberately, then begin a fresh operation before creating the manifest.

### TODO
- [ ] Establish explicit SpecDD ownership or modification authority for `integration/specdd/extension.yml` in a separate authority operation.
- [ ] Validate the manifest against the pinned Spec Kit release.
- [ ] Declare extension identity, version, Spec Kit compatibility, SpecDD tool dependency, and `speckit.specdd.context`.
- [ ] Install the extension locally with Spec Kit development installation support.
- [ ] Verify the context command is discovered by the active integration.
- [ ] Add `validate` and `verify` declarations only after those commands exist.
- [ ] Add hooks only after manual commands are reliable.
- [ ] Confirm uninstall leaves Spec Kit core unchanged.

Exit criteria: the local extension installs without patching Spec Kit core and exposes `speckit.specdd.context`.

## 7. Phase 7 — Implement validation and task partition guidance

Initial deterministic diagnostics: `UNRESOLVED_TARGET`, `MULTI_AUTHORITY_TASK`, `AUTHORITY_VIOLATION`, `STALE_BOUNDARY`.

Agentic classifications: `IMPLEMENTATION_CONFLICT`, `SPEC_EVOLUTION_REQUIRED`, `AUTHORITY_EVOLUTION_REQUIRED`.

### TODO
- [ ] Define diagnostic structure and severity levels: info, warning, error, blocking.
- [ ] Detect tasks whose write targets map to zero, one, or multiple primary authorities.
- [ ] Block unknown/conflicting write authority during implementation.
- [ ] Detect obviously stale boundary data.
- [ ] Preserve feature/user-story grouping while recommending authority-local task decomposition.
- [ ] Preserve Spec Kit task ordering and IDs.
- [ ] Accept legitimate contract work that spans authorities rather than blindly rejecting it.
- [ ] Never change durable SpecDD authority merely to make a task valid.
- [ ] Distinguish implementation conflict, spec evolution, and authority evolution.
- [ ] Add fixture coverage for every diagnostic/classification.

Exit criteria: validation handles local valid work, accidental cross-authority mutation, legitimate multi-domain work, spec evolution, and authority evolution without synchronizing tasks into `.sdd`.

## 8. Phase 8 — Implement `speckit.specdd.verify`

Create `integration/specdd/commands/verify.md`.

### TODO
- [ ] Determine actual changed files from Git.
- [ ] Exclude unrelated generated files from authority checks.
- [ ] Re-resolve SpecDD context for actual changed targets.
- [ ] Compare actual domains with the planned Change Boundary.
- [ ] Detect newly affected domains, invalid writes, stale scope, and unresolved authority.
- [ ] Run or request `specdd lint` as appropriate.
- [ ] Report SpecDD drift and likely missing durable spec evolution separately from feature gaps.
- [ ] Add verification tests, including a feature-correct but authority-invalid implementation.

Exit criteria: verification catches an unauthorized cross-domain change even when feature behavior appears complete.

## 9. Phase 9 — Implement the Spec Kit preset

Create `integration/specdd-preset/preset.yml` and wrappers that compose upstream behavior rather than copying complete templates.

### TODO
- [ ] Verify preset composition syntax against the pinned Spec Kit release.
- [ ] Augment planning with applicable SpecDD context and a concise SpecDD impact summary.
- [ ] Augment task generation with the one-primary-authority heuristic while preserving user-story grouping.
- [ ] Separate ordinary implementation, spec evolution, and authority evolution in task guidance.
- [ ] Augment convergence with SpecDD verification findings while preserving upstream convergence logic.
- [ ] Add `SPECDD_VIOLATION`, `SPECDD_DRIFT`, `MISSING_SPEC_EVOLUTION`, and `AUTHORITY_VIOLATION` convergence diagnostics.
- [ ] Add cross-domain planning/task/convergence tests.

Exit criteria: SpecDD context improves generated plans and tasks before post-generation validation occurs.

## 10. Phase 10 — Add deliberate spec-evolution handling

### TODO
- [ ] Represent `SPEC_EVOLUTION_REQUIRED` explicitly.
- [ ] Represent `AUTHORITY_EVOLUTION_REQUIRED` explicitly.
- [ ] Surface proposed `.sdd` deltas without applying them automatically.
- [ ] End the current authority context after an authority-changing spec edit.
- [ ] Require a fresh Change Boundary before implementation continues.
- [ ] Test a new durable Auth-to-Users contract.
- [ ] Test an intentional change to write authority.
- [ ] Verify newly proposed authority is unusable until re-resolution.

Exit criteria: legitimate architecture evolution works without allowing an operation to self-authorize.

## 11. Phase 11 — Add lifecycle hooks

Only start after context, validate, and verify work manually.

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
- [ ] Unit-test path normalization, boundary construction, schema validation, authority sets, cross-boundary detection, and error normalization.
- [ ] Integration-test real SpecDD CLI success, unresolved paths, invalid specs, multiple domains, and CLI failures.
- [ ] Test local extension/preset installation without upstream patches.
- [ ] Automate semantic scenarios A-E from `docs/spec.md`.
- [ ] Add a regression test for every integration bug found during development.

Exit criteria: deterministic checks are automated and agentic semantic cases have repeatable acceptance procedures.

## 14. Phase 14 — Documentation

### TODO
- [ ] Write the project README after the first vertical slice works.
- [ ] Document installation and local development.
- [ ] Document Change Boundary semantics and regeneration.
- [ ] Document bridge command usage and diagnostics.
- [ ] Document task-partition guidance and why Spec Kit tasks are not synchronized with SpecDD tasks.
- [ ] Document constitution versus root SpecDD responsibilities.
- [ ] Document the authority-snapshot invariant and spec-evolution lifecycle.
- [ ] Add a cross-domain example and troubleshooting for missing CLI/unresolved targets.

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

Stop after the next narrow vertical-slice step:
- [ ] Establish durable SpecDD write authority for `integration/specdd/extension.yml`, then start a fresh operation.
- [ ] Create the local extension manifest.
- [ ] Install the extension with pinned Spec Kit development installation support.
- [ ] Run `speckit.specdd.context` through Spec Kit and regenerate one valid `boundary.json`.

Do not start validation, presets, workflow overlays, or bundle packaging before the installed context command works.

## 20. Definition of done for v0.1

- [ ] Spec Kit core is unmodified.
- [ ] SpecDD core is unmodified.
- [ ] The bridge installs locally as a Spec Kit extension.
- [ ] The bridge uses the real SpecDD resolver.
- [ ] `speckit.specdd.context` generates a valid, rebuildable Change Boundary.
- [ ] `speckit.specdd.validate` recognizes authority and system-evolution issues.
- [ ] `speckit.specdd.verify` checks actual implementation scope.
- [ ] The preset supplies SpecDD context during planning and task generation.
- [ ] Feature user stories may span multiple SpecDD domains while implementation tasks remain authority-local where practical.
- [ ] Spec Kit tasks remain the canonical feature execution tasks.
- [ ] SpecDD remains the canonical persistent system model.
- [ ] Unauthorized cross-domain mutation is detected.
- [ ] Legitimate cross-domain work is representable.
- [ ] Spec evolution is distinct from implementation conflict.
- [ ] Authority evolution requires re-resolution before new rights can be used.
- [ ] Required semantic acceptance tests pass.
- [ ] A clean clone reproduces the development setup from documentation.

## 21. Core implementation constraint

Spec Kit owns the change lifecycle. SpecDD owns persistent system semantics. The bridge resolves, projects, validates, and verifies; it must not become a third competing specification system.
