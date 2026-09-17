# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Implementation strategy

Build the remaining integration in this order:

1. expose `speckit.specdd.context` on top of the Change Boundary adapter,
2. package the context command in the local Spec Kit extension,
3. implement validation and task-partition guidance,
4. implement verification from actual changed files,
5. augment Spec Kit planning, tasks, and convergence,
6. add deliberate spec-evolution handling,
7. add hooks and then a workflow overlay,
8. harden tests, documentation, and compatibility.

Do not begin bundle packaging, automatic `.sdd` editing, or workflow automation before the manual vertical slice works.

The first milestone remains:

context → validate → implement → verify

The pinned SpecDD 1.1.1 resolver contract has been inspected against the two-domain fixture. For both Auth and Users targets, `directories` contains root-to-local resolved context, each resolved spec exposes a repository-relative forward-slash `path`, and section bodies contain the raw `Owns`, `Depends on`, `Forbids`, and other resolved entries needed by the bridge. `rootDirectoryPath` and `targetPath` are host-absolute and platform-specific, so derived bridge state must normalize away those machine-local values. The resolver does not emit a dedicated primary-authority field; the adapter therefore derives primary authority narrowly from the already-resolved spec chain and `Owns` entries while preserving SpecDD path semantics rather than parsing `.sdd` source independently.

Change Boundary v1 now uses JSON Schema Draft 2020-12 at `integration/specdd/schemas/change-boundary.schema.json`. Normalized repository paths are non-empty, repository-relative, forward-slash paths with no absolute prefixes, backslashes, duplicate separators, trailing slash, or `.`/`..` path segments. Resolved spec and authority paths end in `.sdd`. `crossBoundary` is consistent with the number of distinct authority paths: `true` requires at least two and `false` permits at most one. Unresolved entries preserve the original input and may include a normalized path when one exists. Generation metadata records the SpecDD CLI and framework versions but deliberately omits a timestamp so regeneration can remain deterministic. The schema contract is exercised without adding a project dependency by `tests/test_change_boundary_schema.py`.

The Phase 4 adapter is implemented at `integration/specdd/scripts/boundary.py`. It consumes the pinned compact resolver JSON, derives primary authority only from resolved `Owns` entries, validates generated documents against the checked-in schema, emits stable JSON to stdout or atomically to a file, and turns invalid targets, resolver failures, malformed resolver output, and authority ambiguity into explicit unresolved diagnostics. `tests/test_boundary.py` covers normalization, SpecDD glob semantics, authority derivation, schema validation, output modes, and the real two-domain fixture. SpecDD 1.1.1 does not provide a stable version-reporting command for this use, so the adapter reads the installed npm package version and falls back to `npm list --global` while framework version comes from the nearest applicable `.specdd/bootstrap.md`.

---

## 5. Phase 5 — Implement `speckit.specdd.context`

Create `integration/specdd/commands/context.md`.

### TODO

- [ ] Locate the active Spec Kit feature using supported Spec Kit state.
- [ ] Discover candidate targets, preferring explicit paths over inference.
- [ ] Permit an incomplete boundary during early planning.
- [ ] Run the adapter and write `specs/<feature>/.specdd/boundary.json`.
- [ ] Summarize authority domains, unresolved targets, and cross-boundary status.
- [ ] Distinguish unresolved targets from invalid paths.
- [ ] Replace derived state cleanly on rerun.
- [ ] Never edit `.sdd` files from this command.
- [ ] Add a manual end-to-end test.

### Exit criteria

A sample feature can generate and regenerate a valid boundary file.

---

## 6. Phase 6 — Create the Spec Kit extension manifest

Create `integration/specdd/extension.yml`.

### TODO

- [ ] Validate the manifest against the pinned Spec Kit release.
- [ ] Declare extension identity, version, Spec Kit compatibility, SpecDD tool dependency, and `speckit.specdd.context`.
- [ ] Install the extension locally with Spec Kit development installation support.
- [ ] Verify the context command is discovered by the active integration.
- [ ] Add `validate` and `verify` declarations only after those commands exist.
- [ ] Add hooks only after manual commands are reliable.
- [ ] Confirm uninstall leaves Spec Kit core unchanged.

### Exit criteria

The local extension installs without patching Spec Kit core and exposes `speckit.specdd.context`.

---

## 7. Phase 7 — Implement validation and task partition guidance

Initial deterministic diagnostics:

- `UNRESOLVED_TARGET`
- `MULTI_AUTHORITY_TASK`
- `AUTHORITY_VIOLATION`
- `STALE_BOUNDARY`

Agentic classifications:

- `IMPLEMENTATION_CONFLICT`
- `SPEC_EVOLUTION_REQUIRED`
- `AUTHORITY_EVOLUTION_REQUIRED`

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

### Exit criteria

The validator handles local valid work, accidental cross-authority mutation, legitimate multi-domain work, spec evolution, and authority evolution without synchronizing tasks into `.sdd`.

---

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

### Exit criteria

Verification catches an unauthorized cross-domain change even when feature-level behavior appears complete.

---

## 9. Phase 9 — Implement the Spec Kit preset

Create `integration/specdd-preset/preset.yml` and command wrappers that compose upstream behavior rather than copying complete upstream templates.

### TODO

- [ ] Verify preset composition syntax against the pinned Spec Kit release.
- [ ] Augment planning with applicable SpecDD context and a concise SpecDD impact summary.
- [ ] Augment task generation with the one-primary-authority heuristic while preserving user-story grouping.
- [ ] Separate ordinary implementation, spec evolution, and authority evolution in task guidance.
- [ ] Augment convergence with SpecDD verification findings while preserving upstream convergence logic.
- [ ] Add `SPECDD_VIOLATION`, `SPECDD_DRIFT`, `MISSING_SPEC_EVOLUTION`, and `AUTHORITY_VIOLATION` convergence diagnostics.
- [ ] Add cross-domain planning/task/convergence tests.

### Exit criteria

SpecDD context improves generated plans and tasks before post-generation validation occurs.

---

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

### Exit criteria

The integration supports legitimate architecture evolution without allowing an operation to self-authorize.

---

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

### Exit criteria

Normal Spec Kit usage invokes bridge gates at the required lifecycle transitions.

---

## 12. Phase 12 — Add workflow overlay

### TODO

- [ ] Verify overlay syntax against the pinned Spec Kit release.
- [ ] Add deterministic context, validation, pre-implementation authority, and verification steps.
- [ ] Test step ordering and failure propagation.
- [ ] Avoid duplicating equivalent hook behavior.
- [ ] Document the final responsibility split between hooks and overlay steps.

### Exit criteria

Critical authority gates are structurally represented rather than depending only on prompt memory.

---

## 13. Phase 13 — Complete the test matrix

### TODO

- [ ] Unit-test path normalization, boundary construction, schema validation, authority sets, cross-boundary detection, and error normalization.
- [ ] Integration-test real SpecDD CLI success, unresolved paths, invalid specs, multiple domains, and CLI failures.
- [ ] Test local extension/preset installation without upstream patches.
- [ ] Automate semantic scenarios A-E from `docs/spec.md`.
- [ ] Add a regression test for every integration bug found during development.

### Exit criteria

Deterministic checks are automated and agentic semantic cases have repeatable acceptance procedures.

---

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

---

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

---

## 18. Deferred work

Do not implement before v0.1 proves the semantic bridge:

- bundle packaging and public registry publishing,
- automatic `.sdd` editing or approval,
- CI integration,
- rich requirement-to-code traceability,
- graph/IDE visualization,
- automatic task rewriting,
- persistent integration databases,
- cross-repository authority,
- a general policy language for bridge rules.

---

## 19. Next coding session

Stop after the first narrow vertical slice:

- [ ] Implement minimal `speckit.specdd.context` around the completed adapter.
- [ ] Generate and regenerate one valid `boundary.json` through the context command.
- [ ] Create the local extension manifest, install it, and run the context command through Spec Kit.

Do not start validation, presets, workflow overlays, or bundle packaging before this slice works.

---

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

---

## 21. Core implementation constraint

At every implementation decision, preserve this ownership split:

Spec Kit owns the change lifecycle.
SpecDD owns persistent system semantics.
The bridge resolves, projects, validates, and verifies.

The bridge must not become a third competing specification system.
