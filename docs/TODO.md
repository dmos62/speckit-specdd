# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned  
Target: v0.1

## 1. Implementation strategy

Build the integration incrementally in this order:

1. bootstrap the lab,
2. establish a minimal SpecDD fixture,
3. prove machine-readable SpecDD resolution,
4. implement the Change Boundary,
5. expose the context command,
6. implement validation,
7. implement verification,
8. augment Spec Kit planning,
9. augment Spec Kit task generation,
10. augment convergence,
11. add lifecycle integration,
12. test deliberate spec evolution,
13. document and package the v0.1 development setup.

Do not begin with bundle packaging or workflow automation.

The first milestone is successful end-to-end manual use of:

context → validate → implement → verify

---

# 2. Phase 0 — Bootstrap the integration lab

## TODO

- [ ] Create a new Git repository for the integration lab.
- [ ] Install a supported Node.js version required by SpecDD.
- [ ] Install `uv`.
- [ ] Install/pin the chosen Spec Kit release.
- [ ] Install/pin the chosen SpecDD CLI release.
- [ ] Record installed versions in project documentation.
- [ ] Initialize Spec Kit in the repository.
- [ ] Initialize SpecDD in the repository.
- [ ] Run Spec Kit's environment/check command successfully.
- [ ] Run `specdd lint` successfully.
- [ ] Add a `.gitignore` appropriate for the chosen agent/toolchain.
- [ ] Commit the clean initialized baseline before integration work begins.

## Exit criteria

- Spec Kit operates normally with no bridge installed.
- SpecDD operates normally with no bridge installed.
- Both tools coexist in one repository.
- The baseline is committed and reproducible.

---

# 3. Phase 1 — Create the integration source layout

Create a source layout independent from generated Spec Kit installation state.

Proposed structure:

integration/
  specdd/
    extension.yml
    commands/
      context.md
      validate.md
      verify.md
    scripts/
      boundary.py
    schemas/
      change-boundary.schema.json
    tests/

  specdd-preset/
    preset.yml
    commands/
      plan.md
      tasks.md
      converge.md

fixtures/
  minimal-system/

docs/
  spec.md
  implementation-plan.md

## TODO

- [ ] Create `integration/specdd/`.
- [ ] Create extension command directories.
- [ ] Create scripts directory.
- [ ] Create schema directory.
- [ ] Create tests directory.
- [ ] Create `integration/specdd-preset/`.
- [ ] Create preset command directory.
- [ ] Create fixture directory.
- [ ] Keep integration source separate from installed/generated Spec Kit files.
- [ ] Decide whether Python packaging metadata is required for test execution.
- [ ] Add a project-level README later, after the first working vertical slice.

## Exit criteria

- Repository structure clearly separates:
  - integration source,
  - fixtures,
  - documentation,
  - generated Spec Kit state.

---

# 4. Phase 2 — Build the minimal SpecDD fixture

Create a tiny system with two authority domains.

Suggested fixture:

fixtures/minimal-system/
  project.sdd
  src/
    auth/
      auth.sdd
      service.ts
    users/
      users.sdd
      repository.ts

The fixture should express semantics equivalent to:

- Auth owns Auth internals.
- Users owns Users internals.
- Auth may use an approved Users-facing contract.
- Auth may not directly mutate Users internals.

## TODO

- [ ] Create root/project SpecDD specification.
- [ ] Create Auth specification.
- [ ] Create Users specification.
- [ ] Create minimal source files.
- [ ] Confirm `specdd lint` passes against the fixture.
- [ ] Confirm `specdd resolve` can resolve an Auth path.
- [ ] Confirm `specdd resolve` can resolve a Users path.
- [ ] Capture representative machine-readable resolver output in test fixtures if useful.
- [ ] Verify resolver output exposes enough information for the planned Change Boundary.
- [ ] Document any missing resolver information before compensating in bridge code.

## Exit criteria

- The fixture exposes at least two distinct SpecDD-governed domains.
- The fixture can represent both valid and invalid cross-domain writes.
- Resolver JSON is understood well enough to design normalization.

---

# 5. Phase 3 — Define Change Boundary schema v1

Create:

`integration/specdd/schemas/change-boundary.schema.json`

Initial conceptual shape:

{
  "schemaVersion": 1,
  "feature": "...",
  "targets": [
    {
      "path": "...",
      "primaryAuthority": "...",
      "resolvedSpecs": []
    }
  ],
  "authorities": [],
  "crossBoundary": false,
  "unresolved": []
}

## TODO

- [ ] Define JSON Schema draft/version.
- [ ] Define required top-level properties.
- [ ] Define normalized repository-relative path format.
- [ ] Define target object.
- [ ] Define governing specification representation.
- [ ] Define primary authority representation.
- [ ] Define unresolved target representation.
- [ ] Define diagnostic metadata needed for failed resolution.
- [ ] Decide whether generation timestamp belongs in the file.
- [ ] Decide whether tool versions belong in generation metadata.
- [ ] Avoid embedding complete `.sdd` contents.
- [ ] Avoid storing information that cannot be regenerated.
- [ ] Add schema validation tests.

## Design decision

Treat `boundary.json` as disposable derived state.

It must be safe to delete and regenerate.

## Exit criteria

- Boundary schema can represent:
  - one authority,
  - multiple authorities,
  - unresolved paths,
  - a cross-boundary feature.
- Schema contains no unnecessary duplicate source-of-truth data.

---

# 6. Phase 4 — Implement the SpecDD adapter

Create:

`integration/specdd/scripts/boundary.py`

Initial responsibilities:

1. find repository root,
2. accept target paths,
3. normalize paths,
4. invoke `specdd resolve`,
5. parse JSON,
6. normalize output,
7. construct Change Boundary,
8. validate output against schema,
9. write `boundary.json` when requested.

## TODO

- [ ] Implement repository-root discovery.
- [ ] Implement target path normalization.
- [ ] Reject targets outside the repository unless explicitly supported.
- [ ] Invoke the real SpecDD CLI.
- [ ] Use machine-readable output.
- [ ] Capture non-zero exit status.
- [ ] Capture malformed JSON.
- [ ] Normalize resolved spec paths.
- [ ] Derive distinct authority domains.
- [ ] Determine `crossBoundary`.
- [ ] Represent unresolved targets.
- [ ] Validate generated data against Change Boundary schema.
- [ ] Support stdout JSON mode.
- [ ] Support write-to-file mode.
- [ ] Ensure stable output ordering where practical.
- [ ] Add unit tests around normalization.
- [ ] Add integration tests using the real fixture and SpecDD CLI.
- [ ] Do not implement a `.sdd` parser.

## Exit criteria

A command equivalent to:

`boundary.py src/auth/service.ts src/users/repository.ts`

produces a valid Change Boundary showing both domains.

---

# 7. Phase 5 — Implement `speckit.specdd.context`

Create the extension command:

`integration/specdd/commands/context.md`

Responsibilities:

1. identify the active feature,
2. determine available candidate targets,
3. run the boundary adapter,
4. write or refresh:
   `specs/<feature>/.specdd/boundary.json`,
5. summarize:
   - involved authority domains,
   - unresolved targets,
   - cross-boundary status,
   - likely areas requiring attention.

## TODO

- [ ] Determine how the command locates the active Spec Kit feature.
- [ ] Determine how the command obtains target paths before `tasks.md` exists.
- [ ] Prefer explicit paths over inferred paths.
- [ ] Allow empty/incomplete boundaries during early planning.
- [ ] Run the adapter.
- [ ] Create `.specdd/` under the active feature directory.
- [ ] Write `boundary.json`.
- [ ] Provide concise human-readable output.
- [ ] Distinguish unresolved target from invalid target.
- [ ] Ensure rerunning the command replaces derived state cleanly.
- [ ] Ensure the command never edits `.sdd`.
- [ ] Add a manual end-to-end test.

## Exit criteria

For a sample feature, running the context command creates a valid derived boundary file.

This is the first required working vertical slice.

---

# 8. Phase 6 — Create the Spec Kit extension manifest

Create:

`integration/specdd/extension.yml`

Declare:

- extension identity,
- version,
- Spec Kit compatibility,
- SpecDD external tool dependency,
- commands:
  - `speckit.specdd.context`
  - `speckit.specdd.validate`
  - `speckit.specdd.verify`
- bridge scripts,
- lifecycle hooks supported by the installed Spec Kit release.

## TODO

- [ ] Verify current Spec Kit extension manifest schema against installed version.
- [ ] Implement minimal manifest with only `context`.
- [ ] Install extension locally in development mode.
- [ ] Verify Spec Kit discovers the command.
- [ ] Add `validate` declaration after implementation.
- [ ] Add `verify` declaration after implementation.
- [ ] Add hooks only after commands are proven manually.
- [ ] Pin supported Spec Kit version range conservatively.
- [ ] Document SpecDD CLI requirement.
- [ ] Confirm uninstall leaves upstream Spec Kit unchanged.

## Exit criteria

- Local extension installation succeeds.
- `speckit.specdd.context` is available through the chosen agent integration.
- No Spec Kit core files are modified manually.

---

# 9. Phase 7 — Implement validation model

Create:

`integration/specdd/commands/validate.md`

Add deterministic helper code only where needed.

Initial diagnostic taxonomy:

- `UNRESOLVED_TARGET`
- `MULTI_AUTHORITY_TASK`
- `AUTHORITY_VIOLATION`
- `IMPLEMENTATION_CONFLICT`
- `SPEC_EVOLUTION_REQUIRED`
- `AUTHORITY_EVOLUTION_REQUIRED`
- `STALE_BOUNDARY`

Severity levels:

- info,
- warning,
- error,
- blocking.

## TODO

- [ ] Define diagnostic data structure.
- [ ] Define which findings are deterministic.
- [ ] Define which findings require agent reasoning.
- [ ] Detect tasks with target paths in multiple primary authorities.
- [ ] Detect unknown authority for a write target.
- [ ] Detect obviously stale boundary targets.
- [ ] Present task-splitting suggestions.
- [ ] Do not automatically split tasks in v0.1 unless only rewriting generated draft output.
- [ ] Do not modify SpecDD authority to resolve errors.
- [ ] Teach the command to distinguish:
  - accidental implementation conflict,
  - deliberate system-contract evolution.
- [ ] Teach the command to distinguish:
  - spec evolution,
  - authority evolution.
- [ ] Add fixture cases for every diagnostic category.
- [ ] Define blocking behavior before implementation.

## Initial blocking policy

Planning:
- unresolved details may warn.

Task generation:
- unresolved write authority should be prominent.

Implementation:
- unknown or conflicting write authority should block.

Authority evolution:
- always requires a separate re-resolution step before implementation continues.

## Exit criteria

The validator correctly handles:

1. one-domain valid task,
2. accidental cross-authority write,
3. legitimate multi-domain feature,
4. proposed spec evolution,
5. proposed authority evolution.

---

# 10. Phase 8 — Implement task partition guidance

This phase adapts Spec Kit task semantics without replacing them.

Core rule:

> A Spec Kit implementation task should normally have one primary SpecDD authority for its write set.

## TODO

- [ ] Determine how generated Spec Kit tasks expose file paths.
- [ ] Resolve each task's write targets.
- [ ] Map each task to zero, one, or multiple primary authorities.
- [ ] Mark zero-authority tasks for review.
- [ ] Accept one-authority tasks.
- [ ] Analyze multi-authority tasks.
- [ ] Recommend decomposition where appropriate.
- [ ] Keep all decomposed tasks under the same user story when applicable.
- [ ] Preserve Spec Kit dependency ordering.
- [ ] Do not map user stories one-to-one with SpecDD domains.
- [ ] Do not synchronize tasks into `.sdd`.
- [ ] Add test:
  one user story → three authority-local tasks.
- [ ] Add test:
  multi-authority task legitimately represents contract work and should not be blindly rejected.

## Exit criteria

The bridge can explain why a task crosses authority domains and propose a better execution partition without damaging feature cohesion.

---

# 11. Phase 9 — Implement `speckit.specdd.verify`

Create:

`integration/specdd/commands/verify.md`

Verification must use actual changed files rather than trusting the planned boundary.

## TODO

- [ ] Determine changed files from Git.
- [ ] Separate relevant source/spec changes from unrelated generated files.
- [ ] Re-run SpecDD resolution for actual changed targets.
- [ ] Compare actual changed domains with planned Change Boundary.
- [ ] Identify newly affected authority domains.
- [ ] Identify writes that lack valid authority.
- [ ] Run or request `specdd lint`.
- [ ] Detect likely SpecDD drift.
- [ ] Detect changes that appear durable but lack required `.sdd` evolution.
- [ ] Report system-contract violations separately from feature gaps.
- [ ] Do not treat successful feature tests as proof of SpecDD compliance.
- [ ] Add fixture verification tests.

## Exit criteria

Verification catches a deliberately introduced unauthorized cross-domain change even if the Spec Kit feature itself appears functionally complete.

---

# 12. Phase 10 — Implement the Spec Kit preset

Create:

`integration/specdd-preset/preset.yml`

The preset should compose upstream Spec Kit behavior rather than copy complete upstream templates.

## 12.1 Plan augmentation

Create:

`integration/specdd-preset/commands/plan.md`

The wrapper should instruct planning to:

- inspect applicable SpecDD context,
- treat current SpecDD rules as system constraints,
- identify affected authority domains,
- identify cross-boundary contracts,
- identify required durable spec evolution,
- avoid copying complete SpecDD rule bodies into `plan.md`.

## TODO

- [ ] Verify preset composition syntax against installed Spec Kit release.
- [ ] Wrap existing planning behavior.
- [ ] Run SpecDD context before or during implementation design.
- [ ] Add a `SpecDD Impact` section to planned output if useful.
- [ ] Record references to governing SpecDD domains.
- [ ] Do not duplicate full rule text.
- [ ] Add test planning a cross-domain feature.

## 12.2 Task augmentation

Create:

`integration/specdd-preset/commands/tasks.md`

The wrapper should instruct task generation to:

- preserve user-story grouping,
- prefer one primary authority per implementation task,
- separate deliberate SpecDD evolution from ordinary implementation,
- mark authority evolution clearly,
- avoid task synchronization with `.sdd`.

## TODO

- [ ] Wrap upstream task behavior.
- [ ] Add authority-local task-generation rule.
- [ ] Add explicit spec-evolution classification.
- [ ] Add explicit authority-evolution classification.
- [ ] Add test for user story spanning Auth and Users.
- [ ] Confirm upstream task IDs/order still work.

## 12.3 Convergence augmentation

Create:

`integration/specdd-preset/commands/converge.md`

Combined model:

feature intent:
- Spec Kit feature artifacts

system intent:
- effective SpecDD contracts

governance:
- Spec Kit constitution

## TODO

- [ ] Wrap current convergence behavior.
- [ ] Include SpecDD verification findings.
- [ ] Keep feature and system findings separately identifiable.
- [ ] Add diagnostic classes:
  - `SPECDD_VIOLATION`
  - `SPECDD_DRIFT`
  - `MISSING_SPEC_EVOLUTION`
  - `AUTHORITY_VIOLATION`
- [ ] Avoid replacing upstream convergence logic.
- [ ] Add end-to-end convergence test.

## Exit criteria

Spec Kit creates better plans/tasks because SpecDD context is present during generation, not merely checked afterward.

---

# 13. Phase 11 — Add deliberate spec-evolution workflow

Implement the semantic distinction between code change and durable system-specification change.

Expected sequence:

feature request
→ detect required SpecDD evolution
→ propose `.sdd` delta
→ deliberate specification change
→ end current authority context
→ re-resolve
→ implementation

## TODO

- [ ] Define explicit representation of `SPEC_EVOLUTION_REQUIRED`.
- [ ] Define explicit representation of `AUTHORITY_EVOLUTION_REQUIRED`.
- [ ] Ensure validation does not treat either as an ordinary implementation error.
- [ ] Surface proposed `.sdd` changes without automatically applying them.
- [ ] Ensure authority-changing `.sdd` work ends the current authorization context.
- [ ] Require fresh Change Boundary after authority evolution.
- [ ] Add test where Auth requires a new Users-facing contract.
- [ ] Add test where Auth is intentionally granted new modification authority.
- [ ] Verify new authority is not considered active until re-resolution.
- [ ] Document the lifecycle clearly.

## Exit criteria

The integration permits legitimate architecture evolution without allowing an operation to self-authorize.

---

# 14. Phase 12 — Add lifecycle hooks

Only begin this phase after all bridge commands work manually.

Desired lifecycle shape:

plan
→ context

tasks
→ validate

implement
→ validate/re-resolve
→ implementation
→ verify

converge
→ include SpecDD verification

## TODO

- [ ] Verify supported hook names in the pinned Spec Kit version.
- [ ] Add post-plan context hook if reliable.
- [ ] Add post-tasks validation hook.
- [ ] Add pre-implementation blocking validation hook.
- [ ] Add post-implementation verification hook.
- [ ] Evaluate convergence hooks separately.
- [ ] Confirm hook failures are propagated correctly.
- [ ] Confirm mandatory hooks cannot be silently ignored.
- [ ] Avoid depending on undocumented hook behavior.
- [ ] Move critical gates to workflow steps if hook semantics are insufficient.

## Exit criteria

Normal Spec Kit usage invokes the bridge at appropriate lifecycle transitions without manual remembering.

---

# 15. Phase 13 — Add workflow overlay

Add a workflow overlay only after hook behavior is understood.

The overlay should make critical bridge operations explicit and deterministic.

Potential steps:

- after plan: refresh SpecDD context,
- after tasks: validate authority partition,
- before implementation: re-resolve and authorize,
- after implementation: verify actual changes.

## TODO

- [ ] Verify workflow overlay format against pinned Spec Kit version.
- [ ] Create development overlay.
- [ ] Add deterministic context step.
- [ ] Add deterministic validation step.
- [ ] Add deterministic pre-implementation authority gate.
- [ ] Add deterministic verification step.
- [ ] Test ordering.
- [ ] Test failure behavior.
- [ ] Ensure workflow does not duplicate equivalent extension-hook behavior.
- [ ] Decide final responsibility split between hooks and overlay.

## Exit criteria

Critical validation is structurally represented in the workflow rather than depending exclusively on prompt instructions.

---

# 16. Phase 14 — Testing strategy

Testing should occur at four levels.

## 16.1 Unit tests

Test:

- path normalization,
- Change Boundary construction,
- schema validation,
- authority-set calculation,
- cross-boundary detection,
- error normalization.

## 16.2 Adapter integration tests

Use the real SpecDD CLI against fixture repositories.

Test:

- successful resolution,
- unresolved path,
- invalid `.sdd`,
- multiple domains,
- CLI failure,
- malformed/unsupported output if mockable.

## 16.3 Spec Kit integration tests

Test local extension/preset installation.

Validate:

- commands are visible,
- preset wraps upstream behavior,
- lifecycle invocation works,
- no upstream files are manually patched.

## 16.4 Semantic acceptance tests

Required cases:

### A. Local valid change

Expected:
- valid.

### B. Unauthorized cross-domain mutation

Expected:
- `AUTHORITY_VIOLATION`.

### C. Multi-domain feature with authority-aligned tasks

Expected:
- valid.

### D. Multi-domain task that should be decomposed

Expected:
- warning/error plus suggested decomposition.

### E. Genuine durable system-contract change

Expected:
- `SPEC_EVOLUTION_REQUIRED`.

### F. Genuine ownership/write-authority change

Expected:
- `AUTHORITY_EVOLUTION_REQUIRED`,
- implementation cannot continue under newly proposed authority until re-resolution.

### G. Boundary drift

Plan mentions Auth only; implementation also changes Users.

Expected:
- verification detects additional domain,
- boundary is considered stale/incomplete.

### H. Feature succeeds but system contract is violated

Expected:
- Spec Kit feature success does not suppress SpecDD violation.

## TODO

- [ ] Create test matrix.
- [ ] Automate deterministic tests.
- [ ] Document manual agent-driven semantic tests.
- [ ] Add regression test for every integration bug found during development.

---

# 17. Phase 15 — Documentation

Required v0.1 documentation:

- project README,
- installation,
- local development,
- architecture,
- Change Boundary description,
- command reference,
- semantic classifications,
- spec-evolution workflow,
- troubleshooting,
- compatibility versions.

## TODO

- [ ] Write README after first vertical slice works.
- [ ] Document exact install commands.
- [ ] Document dev extension installation.
- [ ] Document how to regenerate `boundary.json`.
- [ ] Explain that boundary state is derived.
- [ ] Explain one-primary-authority task heuristic.
- [ ] Explain constitution versus root SpecDD.
- [ ] Explain why Spec Kit tasks and SpecDD tasks are not synchronized.
- [ ] Explain authority-snapshot invariant.
- [ ] Add sample cross-domain feature.
- [ ] Add troubleshooting for missing SpecDD CLI.
- [ ] Add troubleshooting for unresolved targets.

---

# 18. Phase 16 — v0.1 hardening

## TODO

- [ ] Pin tested Spec Kit version range.
- [ ] Pin/test SpecDD CLI version range.
- [ ] Add compatibility assertions where possible.
- [ ] Ensure errors mention the failed external dependency clearly.
- [ ] Ensure path handling works on supported operating systems.
- [ ] Ensure generated state is deterministic enough for testing.
- [ ] Decide whether `.specdd/boundary.json` should be committed or ignored.
- [ ] Recommended default: treat boundary as generated state unless a strong review use case emerges.
- [ ] Ensure uninstall leaves no patched upstream files.
- [ ] Run all acceptance scenarios from a clean clone.
- [ ] Tag v0.1 only after clean-clone reproduction succeeds.

---

# 19. Deferred work

Do not implement the following until after v0.1 proves the semantic model:

- [ ] Spec Kit bundle packaging.
- [ ] Public registry publishing.
- [ ] Automated `.sdd` editing.
- [ ] Automatic acceptance of proposed SpecDD evolution.
- [ ] Rich requirement-to-code traceability.
- [ ] CI integration.
- [ ] Graph visualization.
- [ ] IDE integration.
- [ ] Automatic task rewriting after validation.
- [ ] Persistent integration database.
- [ ] Cross-repository SpecDD authority.
- [ ] Full formal policy language for bridge rules.

---

# 20. Recommended first coding session

The first implementation session should stop after proving one narrow path.

## TODO

- [ ] Bootstrap repo.
- [ ] Initialize Spec Kit.
- [ ] Initialize SpecDD.
- [ ] Create minimal Auth/Users fixture.
- [ ] Run `specdd resolve` manually on both domains.
- [ ] Inspect real JSON output.
- [ ] Finalize Change Boundary schema based on actual resolver output.
- [ ] Implement `boundary.py`.
- [ ] Generate one valid `boundary.json`.
- [ ] Add tests for the adapter.
- [ ] Implement minimal `speckit.specdd.context`.
- [ ] Install extension locally.
- [ ] Run context command successfully through Spec Kit.

Stop there.

Do not implement validation, presets, workflow overlays, or bundle packaging until this vertical slice works.

---

# 21. Definition of done for v0.1

v0.1 is done when:

- [ ] Spec Kit core is unmodified.
- [ ] SpecDD core is unmodified.
- [ ] The bridge is installable locally as a Spec Kit extension.
- [ ] The bridge uses the real SpecDD resolver.
- [ ] `speckit.specdd.context` generates a valid Change Boundary.
- [ ] `speckit.specdd.validate` recognizes authority and system-evolution issues.
- [ ] `speckit.specdd.verify` checks actual implementation scope.
- [ ] The preset provides SpecDD context during planning.
- [ ] The preset encourages authority-local implementation tasks.
- [ ] Feature user stories may span multiple SpecDD domains.
- [ ] Spec Kit tasks remain the canonical feature execution tasks.
- [ ] SpecDD remains the canonical persistent system model.
- [ ] Derived integration state can be deleted and rebuilt.
- [ ] Unauthorized cross-domain mutation is detected.
- [ ] Legitimate cross-domain work is representable.
- [ ] Spec evolution is distinct from implementation conflict.
- [ ] Authority evolution requires re-resolution before new rights can be used.
- [ ] All required semantic acceptance tests pass.
- [ ] A clean clone can reproduce the development setup from documentation.

---

# 22. Core implementation constraint

At every implementation decision, prefer the option that preserves this architecture:

Spec Kit
    owns change lifecycle

SpecDD
    owns persistent system semantics

Bridge
    resolves, projects, validates, and verifies

The bridge must not become a third competing specification system.
