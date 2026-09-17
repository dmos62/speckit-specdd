# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Implementation strategy

Build the remaining integration in this order:

1. augment Spec Kit planning, tasks, and convergence,
2. add deliberate spec-evolution handling,
3. add hooks and then a workflow overlay,
4. harden tests, documentation, and compatibility.

Do not begin bundle packaging, automatic `.sdd` editing, or workflow automation before the manual vertical slice works.

The manual context → validate → implement → verify vertical slice is now present.

The pinned SpecDD 1.1.1 resolver contract has been inspected against the two-domain fixture. `directories` contains root-to-local resolved context, resolved specs expose repository-relative forward-slash `path` values, and section bodies contain the raw resolved entries needed by the bridge. Host-absolute `rootDirectoryPath` and `targetPath` values must not enter derived state. Because the resolver has no dedicated primary-authority field, the adapter derives authority narrowly from resolved `Owns` entries without parsing `.sdd` independently.

Change Boundary v1 uses JSON Schema Draft 2020-12 at `integration/specdd/schemas/change-boundary.schema.json`. Paths are non-empty repository-relative forward-slash paths without absolute prefixes, backslashes, duplicate separators, trailing slash, or `.`/`..` segments. Resolved spec and authority paths end in `.sdd`. `crossBoundary` is derived from distinct authorities. Unresolved entries preserve original input and optional normalized path. Generation metadata records SpecDD CLI/framework versions without a timestamp so regeneration remains deterministic.

The adapter at `integration/specdd/scripts/boundary.py` consumes compact resolver JSON, derives primary authority from resolved `Owns`, validates the checked-in schema, writes atomically, and normalizes invalid targets, resolver failures, malformed output, and authority ambiguity into structured unresolved diagnostics. Tests cover normalization, SpecDD glob semantics, authority derivation, schema validation, output modes, and the real two-domain fixture. SpecDD CLI version detection reads the installed npm package and falls back to `npm list --global`; framework version comes from the nearest `.specdd/bootstrap.md`.

The context command source at `integration/specdd/commands/context.md` resolves the active feature through Spec Kit state, prefers explicit user targets, otherwise discovers exact targets from `tasks.md` before `plan.md`, and delegates normalization, resolver, ownership, schema validation, and atomic replacement to the adapter. Intended-but-missing paths remain unresolved diagnostics. If no target is named, stale derived boundary state is removed. The command reports authorities, cross-boundary status, and unresolved diagnostics by code.

The extension manifest at `integration/specdd/extension.yml` is authored under `integration/specdd/extension.sdd`. It declares extension version `0.1.0`, exact Spec Kit `1.0.7` compatibility, required SpecDD CLI `1.1.1`, and the context, validation, and verification bridge commands.

Local development installation is validated against Spec Kit `1.0.7`. The generic integration registers bridge commands from the extension manifest and removes generated commands during uninstall. The lifecycle smoke treats `.specify/extensions/.registry` as generated Spec Kit bookkeeping: it rejects semantic registry changes, tolerates Spec Kit's whitespace-only rewrite, restores tracked bytes after the check, and verifies that install/uninstall leaves no generated extension or command state behind.

Deterministic validation is implemented by `integration/specdd/scripts/validation.py`. It reads the validated Change Boundary plus exact paths from Spec Kit `tasks.md`, preserves task order, IDs, and user-story labels, and classifies task write sets as `NO_WRITE_TARGETS`, `SPEC_ONLY`, `NORMAL`, `CROSS_BOUNDARY`, or `UNRESOLVED`. Its stable diagnostics are `UNRESOLVED_TARGET`, `MULTI_AUTHORITY_TASK`, `STALE_BOUNDARY`, and `AUTHORITY_VIOLATION`, with `info`, `warning`, `error`, and `blocking` severity semantics. Multi-authority work is advisory rather than automatically invalid; unknown or conflicting authority blocks at the implementation stage. The validator does not parse `.sdd`, rewrite tasks, or alter authority.

The validation command at `integration/specdd/commands/validate.md` keeps architectural judgment outside deterministic mechanics. It uses multi-authority groups for decomposition guidance while preserving feature and user-story cohesion, and distinguishes `IMPLEMENTATION_CONFLICT`, `SPEC_EVOLUTION_REQUIRED`, and `AUTHORITY_EVOLUTION_REQUIRED` when reasoning about intent. Authority evolution must end the current authority context and be followed by fresh Change Boundary resolution before implementation.

Actual-change verification is implemented by `integration/specdd/scripts/verification.py`. It reads Git porcelain state with rename detection disabled so source and destination mutations remain distinct, excludes the active Spec Kit feature directory plus generated `.specify/` and `.specify-agent/` state from implementation authority checks, and reports changed `.sdd` and root `.specdd/` control files separately. Existing implementation writes receive fresh Change Boundary resolution; deleted writes are checked against the planned authority snapshot because they no longer exist for resolver input. A new or changed authority is a blocking `AUTHORITY_VIOLATION`, while an unplanned path inside an already planned authority is `SPECDD_DRIFT`. Changed `.sdd` files never self-authorize the current operation. Verification also records `specdd lint` and blocks on lint failure.

The verification command at `integration/specdd/commands/verify.md` preserves the planned boundary as the authority snapshot, delegates Git and resolver mechanics to the verification script, and keeps deterministic authority findings separate from feature convergence and agentic `MISSING_SPEC_EVOLUTION` reasoning. Fixture tests cover a valid local change and a feature-correct but unauthorized Users-domain mutation under an Auth-only planned boundary.

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

Start Phase 9 with the Spec Kit preset:
- [ ] Inspect the pinned Spec Kit `1.0.7` preset composition contract rather than guessing its syntax.
- [ ] Add the smallest planning wrapper that supplies current SpecDD context without copying upstream planning templates.
- [ ] Preserve user-story grouping while making authority-local implementation work visible during task generation.
- [ ] Add preset installation and cross-domain behavior tests before lifecycle hooks.

Do not start hooks, workflow overlays, or bundle packaging before preset composition works against the pinned release.

## 20. Definition of done for v0.1

- [ ] Spec Kit core is unmodified.
- [ ] SpecDD core is unmodified.
- [x] The bridge installs locally as a Spec Kit extension.
- [x] The bridge uses the real SpecDD resolver.
- [x] `speckit.specdd.context` generates a valid, rebuildable Change Boundary through its adapter.
- [x] `speckit.specdd.validate` recognizes authority and system-evolution issues.
- [x] `speckit.specdd.verify` checks actual implementation scope.
- [ ] The preset supplies SpecDD context during planning and task generation.
- [ ] Feature user stories may span multiple SpecDD domains while implementation tasks remain authority-local where practical.
- [ ] Spec Kit tasks remain the canonical feature execution tasks.
- [ ] SpecDD remains the canonical persistent system model.
- [x] Unauthorized cross-domain mutation is detected.
- [x] Legitimate cross-domain work is representable.
- [x] Spec evolution is distinct from implementation conflict.
- [x] Authority evolution requires re-resolution before new rights can be used.
- [ ] Required semantic acceptance tests pass.
- [ ] A clean clone reproduces the development setup from documentation.

## 21. Core implementation constraint

Spec Kit owns the change lifecycle. SpecDD owns persistent system semantics. The bridge resolves, projects, validates, and verifies; it must not become a third competing specification system.
