# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Current baseline

The manual context → validate → implement → verify vertical slice is present.

Compatibility remains pinned to Node.js 22+, Spec Kit `1.0.7`, SpecDD CLI `1.1.1`, and SpecDD framework `1.5`. Direct compatibility evidence is intentionally narrower than the prerequisite syntax: Spec Kit `1.0.7`, SpecDD CLI `1.1.1`, and framework `1.5` are the only tested tool versions currently claimed. The 2026-09-17 evidence host was Windows 10 `10.0.19045` on AMD64 and Spec Kit reported Python `3.12.11`; other operating systems, Python versions, and adjacent tool versions remain unverified. Bootstrap check output records the exact Node and bridge Python versions for future evidence.

Phase 15 path handling is hardened around concrete repository paths without broadening operating-system claims. Repository-relative `/` and `\` forms normalize to repository `/` form, the Windows evidence path covers drive-qualified absolute targets inside the repository, foreign absolute path styles are rejected before resolver or active-feature use, backticked task paths preserve spaces and literal bracket/brace characters, wildcard `*` and `?` task patterns remain non-exact, and Git porcelain `-z --no-renames` coverage preserves paths containing spaces and bracket characters. Conditional non-Windows checks are regression coverage only; they do not establish support for an unexercised host.

Change Boundary v1 is defined by `integration/specdd/schemas/change-boundary.schema.json`. The adapter uses the real SpecDD resolver, derives authority only from resolved `Owns` entries, keeps derived state deterministic, and normalizes invalid targets, resolver failures, malformed output, and ownership ambiguity into structured unresolved diagnostics.

The default feature Change Boundary tracking policy is confirmed for v0.1. Repository ignore policy covers `specs/*/.specdd/boundary.json`, no feature Change Boundary is currently tracked, and regression coverage verifies that a representative feature boundary is ignored and that no feature boundary is present in the Git index. `boundary.json` therefore remains generated, uncommitted, disposable cache state reconstructed from Spec Kit feature artifacts and the current SpecDD hierarchy; no ignore-file change is required.

Phase 15 deterministic-output hardening keeps bridge-owned data stable without treating generated Spec Kit materializations as canonical source. Change Boundary generation already sorts its path- and authority-derived collections and carries no timestamp. Validation and verification JSON serialization now sorts mapping keys, embedded SpecDD command diagnostics normalize repository-root paths and line endings, and workflow context summaries report repository-relative boundary paths instead of host-specific absolute paths. Installed preset composition, extension hook bookkeeping, and workflow-overlay materialization remain tested semantically because pinned Spec Kit may legitimately reserialize generated content.

The bridge commands provide context generation, task validation, implementation authorization, and actual-change verification. Deliberate `.sdd` evolution remains separate from implementation authority and the authority-snapshot invariant remains enforced.

External dependency hardening keeps infrastructure failures distinct from authority diagnostics. Bootstrap reports missing Git, Node.js, npm, uv, Codex, Spec Kit, and SpecDD with dependency-specific remediation; structural workflow steps fail with status `2` when uv is absent; adapter and verification entry points report missing SpecDD or Git as infrastructure errors. Resolver failures and malformed resolver output remain `RESOLUTION_FAILED`, nonzero `specdd lint` remains `SPECDD_VIOLATION`, deterministic gate findings use status `1`, and bridge setup/runtime failures use status `2`.

Phase 9 preset composition is implemented at `integration/specdd-preset/`. The pinned Spec Kit `1.0.7` preset contract stores command overrides in `provides.templates` with `type: "command"` and supports append composition.

Pinned Spec Kit `1.0.7` deliberately excludes the `generic` integration from command registration. The supported local strategy is the registrar-backed `codex` integration, which materializes Spec Kit and extension commands under `.agents/skills`. Repository bootstrap selects or switches to Codex through supported Spec Kit commands and installs the local bridge extension and preset from canonical source.

The isolated Codex preset smoke compares semantic upstream skill bodies after preset removal. Spec Kit `1.0.7` may reserialize YAML frontmatter and add a registrar-generated `# Speckit ... Skill` heading while restoring a core skill; those serializer-only differences are ignored while the original command body and absence of the SpecDD augmentation remain required.

Uninstall cleanliness is confirmed through the isolated Codex installation smoke. The test removes the bridge preset, extension, and workflow overlay through supported Spec Kit commands; verifies the composed upstream command bodies are restored semantically; verifies bridge command skills are removed; verifies bridge hook registrations are absent; and verifies the workflow overlay is no longer installed. The supported uninstall path therefore leaves no bridge patch in the upstream command surfaces that the integration composes.

The extension retains mandatory lifecycle hooks for agent-facing context, validation, authorization, and verification when commands are used directly. Hook dispatch remains agent-mediated and is not the structural enforcement boundary.

The structural workflow overlay is implemented at `integration/specdd/workflow-overlay.yml` and is installed through `specify workflow overlay add`. It adds deterministic shell steps after planning, after task generation, before implementation, and after implementation. The task gate refreshes the Change Boundary from exact task targets before validation; authorization reuses that snapshot without refresh; verification compares actual Git writes with the same planned snapshot and fresh resulting authority.

`integration/specdd/scripts/workflow_gate.py` resolves the active Spec Kit feature and delegates to the existing boundary, validation, and verification mechanics. Validation and verification CLIs support failure thresholds so deterministic `error` or `blocking` findings return nonzero status when invoked as workflow gates. The overlay does not set `continue_on_error`, so failures halt workflow execution structurally.

Generated workflow-overlay state is not canonical. If `bash scripts/bootstrap.sh --check` reports that `specdd-bridge` is not installed, run `bash scripts/bootstrap.sh` once to rematerialize the supported overlay state before using check mode again.

Phase 10 deliberate spec-evolution handling remains implemented without adding another source of truth. Evolution tasks use ordinary task-text prefixes `SPEC_EVOLUTION_REQUIRED:` and `AUTHORITY_EVOLUTION_REQUIRED:`; validation requires `.sdd`-only evolution scope and records whether fresh Change Boundary resolution is required.

Phase 13 test-matrix coverage is complete. Real SpecDD CLI fixture coverage includes deterministic multi-domain resolution, missing-target preservation, resolver execution failure normalization, and invalid-spec lint failure. Semantic scenarios A-E from `docs/spec.md` are explicitly mapped to fixture acceptance tests for local change, unauthorized cross-domain mutation, legitimate cross-domain work, deliberate spec evolution, and authority re-resolution.

Pinned Spec Kit `1.0.7` supports project workflow overlays with `id`, `extends`, optional priority and enabled state, and step edits using `insert_before`, `insert_after`, `replace`, or `remove`. Project overlays are installed through `specify workflow overlay add` rather than by editing `.specify/workflows/` directly. Workflow step failure halts execution unless `continue_on_error: true` is explicitly configured.

Phase 14 development-host installation and rematerialization are documented in `docs/development.md`, including the supported Codex integration, the pinned `generic` registration limitation, and supported extension, preset, and workflow-overlay commands.

The user-facing root `README.md` is governed by `README.sdd` and documents the responsibility split, bootstrap path, generated-state boundary, normal authority-aware lifecycle, specification-evolution invariant, cross-domain model, command usage, lifecycle-specific inputs and outputs, deterministic diagnostics, constitution-versus-root-SpecDD responsibilities, and common troubleshooting. Direct command hooks are distinguished from structural workflow enforcement.

Focused Change Boundary documentation is implemented at `docs/change-boundary.md` under `docs/change-boundary.sdd`. The guide documents lifecycle-specific target discovery, deterministic regeneration, unresolved handling, stale-boundary behavior, authority-snapshot preservation, disposable derived state, and the generated/uncommitted default tracking policy without duplicating installation or maintenance procedures.

Compatibility assertions guard the exact Spec Kit, SpecDD CLI, and SpecDD framework pins across canonical bootstrap and manifest source. No semantic version range broader than directly exercised versions is treated as tested compatibility.

## 15. Phase 15 — v0.1 hardening

### TODO

- [ ] Re-run all acceptance scenarios from a clean clone.
- [ ] Tag v0.1 only after clean-clone reproduction succeeds.

## 18. Deferred work

Do not implement before v0.1 proves the semantic bridge: bundle/public registry publishing, automatic `.sdd` editing or approval, CI integration, rich requirement-to-code traceability, graph/IDE visualization, automatic task rewriting, persistent integration databases, cross-repository authority, or a general bridge-policy language.

## 19. Next coding session

Re-run the v0.1 acceptance evidence from a clean clone of committed repository state.

The clean clone must start without relying on current generated Spec Kit materializations or feature Change Boundaries. Run the documented bootstrap path so the Codex integration, bridge extension, preset, workflow overlay, and SpecDD framework state are materialized through their supported tools.

At minimum, reproduce:

    bash scripts/bootstrap.sh
    bash scripts/bootstrap.sh --check
    uv run --no-project python -m unittest discover -s tests -p 'test_*.py'
    specdd lint tests/fixtures/specdd-two-domain
    git diff --check
    git status --short

The full test suite contains the fixture acceptance coverage for semantic scenarios A-E. Confirm those tests execute successfully rather than relying only on prior working-tree results.

Review the final clean-clone Git status so generated or ignored state is not mistaken for canonical source. Feature Change Boundaries should remain absent from the Git index and reconstructible from canonical inputs.

Record the exact host and tool versions exercised by the clean-clone run and any expected generated-state differences. Do not tag v0.1 until this reproduction succeeds.

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
- [x] Required semantic acceptance tests pass.
- [ ] A clean clone reproduces the development setup from documentation.

## 21. Core implementation constraint

Spec Kit owns the change lifecycle. SpecDD owns persistent system semantics. The bridge resolves, projects, validates, and verifies; it must not become a third competing specification system.
