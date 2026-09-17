# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned  
Target: v0.1

## 1. Implementation strategy

Build the integration in this order:

1. finish the bootstrap gate,
2. create the integration source layout,
3. establish a minimal two-domain SpecDD fixture,
4. inspect real machine-readable SpecDD resolution,
5. define and implement Change Boundary v1,
6. expose `speckit.specdd.context`,
7. implement validation and task-partition guidance,
8. implement verification from actual changed files,
9. augment Spec Kit planning, tasks, and convergence,
10. add deliberate spec-evolution handling,
11. add hooks and then a workflow overlay,
12. harden tests, documentation, and compatibility.

Do not begin bundle packaging, automatic `.sdd` editing, or workflow automation before the manual vertical slice works.

The first milestone remains:

context → validate → implement → verify

---

## 2. Phase 0 — Bootstrap gate

Bootstrap automation and compatibility pins live in `scripts/bootstrap.sh` and `docs/development.md`.

### TODO

- [ ] Run `bash scripts/bootstrap.sh` from the repository root.
- [ ] Review the generated Spec Kit and SpecDD baseline for unexpected files.
- [ ] Run `bash scripts/bootstrap.sh --check` successfully.
- [ ] Commit the clean initialized baseline before integration work begins.
- [ ] Delete `HUMAN-REQUEST.md` after the bootstrap output has been reviewed.

### Exit criteria

- Spec Kit operates normally with no bridge installed.
- SpecDD operates normally with no bridge installed.
- Both tools coexist in one repository.
- The pinned baseline is reproducible from `docs/development.md`.
- The initialized baseline is committed and the worktree is clean.

---

## 3. Phase 1 — Create the integration source layout

### TODO

- [ ] Create `integration/specdd/commands/`, `scripts/`, `schemas/`, and `tests/`.
- [ ] Create `integration/specdd-preset/commands/`.
- [ ] Create `fixtures/minimal-system/`.
- [ ] Keep integration source separate from `.specify/` installed/generated state.
- [ ] Decide whether Python packaging metadata is needed for test execution.

### Exit criteria

Integration source, fixtures, documentation, and generated Spec Kit state have clear ownership and separate locations.

---

## 4. Phase 2 — Build the minimal SpecDD fixture

### TODO

- [ ] Create the root project spec.
- [ ] Create independent Auth and Users specs.
- [ ] Create minimal source files owned by those domains.
- [ ] Encode an approved Auth-to-Users read/dependency contract without granting Auth write authority over Users internals.
- [ ] Confirm `specdd lint` passes.
- [ ] Resolve one Auth path and one Users path with machine-readable output.
- [ ] Capture representative resolver output only if it materially simplifies deterministic tests.
- [ ] Document resolver information that is missing before adding bridge-side compensation.

### Exit criteria

The fixture supports valid local writes, invalid cross-domain writes, and legitimate multi-domain feature work.

---

## 5. Phase 3 — Define Change Boundary schema v1

Create `integration/specdd/schemas/change-boundary.schema.json`.

### TODO

- [ ] Choose and declare the JSON Schema draft.
- [ ] Define required top-level properties and repository-relative path rules.
- [ ] Define target, primary-authority, resolved-spec, and unresolved-target representations.
- [ ] Define diagnostic generation metadata without copying complete `.sdd` rules.
- [ ] Decide whether timestamps and tool versions belong in generation metadata.
- [ ] Add schema validation tests for one authority, multiple authorities, unresolved paths, and cross-boundary features.

### Exit criteria

`boundary.json` is disposable, reconstructible, schema-valid derived state and is not a second SpecDD database.

---

## 6. Phase 4 — Implement the SpecDD adapter

Create `integration/specdd/scripts/boundary.py`.

### TODO

- [ ] Discover the repository root.
- [ ] Normalize repository-relative targets and reject unsupported outside-root paths.
- [ ] Invoke the real `specdd resolve` command with machine-readable output.
- [ ] Normalize non-zero exits and malformed JSON into explicit unresolved diagnostics.
- [ ] Normalize resolved spec paths and determine primary authority where possible.
- [ ] Derive the distinct authority set and `crossBoundary` flag.
- [ ] Validate generated output against the Change Boundary schema.
- [ ] Support stdout JSON and write-to-file modes.
- [ ] Make ordering stable where practical.
- [ ] Add unit tests for normalization and integration tests against the real fixture.
- [ ] Do not implement a `.sdd` parser.

### Exit criteria

Resolving one Auth target and one Users target produces a valid Change Boundary containing both authority domains.

---

## 7. Phase 5 — Implement `speckit.specdd.context`

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

## 8. Phase 6 — Create the Spec Kit extension manifest

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

## 9. Phase 7 — Implement validation and task partition guidance

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

## 10. Phase 8 — Implement `speckit.specdd.verify`

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

## 11. Phase 9 — Implement the Spec Kit preset

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

## 12. Phase 10 — Add deliberate spec-evolution handling

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

## 13. Phase 11 — Add lifecycle hooks

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

## 14. Phase 12 — Add workflow overlay

### TODO

- [ ] Verify overlay syntax against the pinned Spec Kit release.
- [ ] Add deterministic context, validation, pre-implementation authority, and verification steps.
- [ ] Test step ordering and failure propagation.
- [ ] Avoid duplicating equivalent hook behavior.
- [ ] Document the final responsibility split between hooks and overlay steps.

### Exit criteria

Critical authority gates are structurally represented rather than depending only on prompt memory.

---

## 15. Phase 13 — Complete the test matrix

### TODO

- [ ] Unit-test path normalization, boundary construction, schema validation, authority sets, cross-boundary detection, and error normalization.
- [ ] Integration-test real SpecDD CLI success, unresolved paths, invalid specs, multiple domains, and CLI failures.
- [ ] Test local extension/preset installation without upstream patches.
- [ ] Automate semantic scenarios A-H from `docs/spec.md`.
- [ ] Add a regression test for every integration bug found during development.

### Exit criteria

Deterministic checks are automated and agentic semantic cases have repeatable acceptance procedures.

---

## 16. Phase 14 — Documentation

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

## 17. Phase 15 — v0.1 hardening

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

After the bootstrap gate is complete, stop after the first narrow vertical slice:

- [ ] Create the Auth/Users fixture.
- [ ] Inspect real JSON from `specdd resolve` for both domains.
- [ ] Finalize Change Boundary v1 from actual resolver output.
- [ ] Implement and test `boundary.py`.
- [ ] Generate one valid `boundary.json`.
- [ ] Implement minimal `speckit.specdd.context`.
- [ ] Install the extension locally and run the context command through Spec Kit.

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
