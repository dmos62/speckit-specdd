# Implementation TODO

The P0 items below are derived from `docs/TECH-DEBT.md` and ordered for authority correctness. The immutable
authorization-snapshot item is omitted because the current iteration implements it by preserving the successfully
validated Change Boundary in worktree Git metadata and making verification consume that snapshot.

## P0 — Intended new implementation targets

- [ ] Support intended non-existent ordinary files without treating all creation as unresolved.
  - Determine whether SpecDD CLI `1.1.1` exposes enough resolver information for intended-path authority.
  - Prefer resolver-backed authority instead of extending the bridge's local `.sdd` interpretation.
  - If the CLI cannot answer intended-path authority safely, fail explicitly with a documented unsupported-creation
    diagnostic rather than implying that all creation is forbidden by SpecDD.
  - Cover exact ownership, directory ownership, glob ownership, no authority, and ambiguous authority.
  - Keep `.sdd` evolution paths excluded from implementation boundary targets.
  - Completion: task-stage and authorization behavior matches SpecDD's intended-path rules without inventing authority.

## P0 — Modification permission distinct from ownership

- [ ] Project `Can modify` separately from primary `Owns` authority.
  - Define the deterministic representation for owning authority versus operation modification permission.
  - Preserve the owning spec as the target's authoritative contract.
  - Resolve and obey the target owning spec when another authority receives non-owning modification permission.
  - Reject cross-owned writes that have no applicable `Can modify` grant.
  - Add fixture coverage for permitted and denied cross-owned writes.
  - Avoid treating a multi-authority task warning as proof that every write is permitted.
  - Completion: authorization answers both who owns each target and whether the operation may modify it.

## P0 — Unplanned specification edits

- [ ] Treat changed `.sdd` files as planned evolution targets rather than automatically informational.
  - Preserve exact `.sdd` targets from explicit evolution tasks outside the implementation Change Boundary.
  - Compare actual changed specifications with planned evolution targets during verification.
  - Block or require mandatory review for specification edits that were not deliberately selected.
  - Preserve the rule that a changed specification never authorizes implementation in the same operation.
  - Add tests for planned, unplanned, added, modified, and deleted `.sdd` files.
  - Completion: arbitrary specification changes cannot pass verification merely as `SPEC_EVOLUTION_PRESENT`.

## P0 — Bootstrap control-file authority

- [ ] Enforce SpecDD bootstrap control-file edit rules during verification.
  - Distinguish immutable `.specdd/bootstrap.md` from explicitly editable project/local overrides.
  - Represent whether a control-file change was selected by the operator or authorized workflow.
  - Block immutable or unplanned control-state changes instead of reporting all of them as warnings.
  - Keep generated/local preferences separate from shared canonical control state.
  - Add tests for immutable bootstrap, project override, local override, and unrelated root `.specdd/` changes.
  - Completion: verification applies the bootstrap contract instead of only classifying control paths.

## P0 — SpecDD state fingerprinting

- [ ] Detect governing SpecDD contract changes between boundary generation and authorization.
  - Define a deterministic identity for the effective SpecDD state used by each resolved target.
  - Include inherited and referenced governing context that can change behavior even when primary ownership is stable.
  - Store the identity in derived boundary state or adjacent deterministic metadata without copying rule text.
  - Recompute and compare it before authorization.
  - Keep the immutable authorization snapshot as the historical post-authorization reference.
  - Add tests for ownership-preserving `Must`, `Forbids`, reference, and governing-chain changes.
  - Completion: authorization rejects a boundary generated from materially different SpecDD contracts.

## P0 — Change Boundary semantic consistency

- [ ] Validate cross-field invariants before trusting a Change Boundary.
  - Require unique resolved target paths.
  - Require `authorities` to equal the distinct non-null target `primaryAuthority` values.
  - Require `crossBoundary` to agree with that authority set.
  - Prevent one path from appearing as both resolved and unresolved.
  - Validate candidate authorities and resolved spec relationships where deterministically knowable.
  - Decide whether nullable `primaryAuthority` remains a supported v1 representation or is removed.
  - Add adapter-level invariant tests separate from JSON Schema shape tests.
  - Completion: a shape-valid but semantically corrupted boundary cannot influence authorization or verification.

## P0 — Operation-scoped Git baseline

- [ ] Bind verification to the implementation operation rather than the entire dirty worktree.
  - Record an authorization-time Git baseline adjacent to operation authorization evidence.
  - Define handling for tracked modifications, staged changes, untracked files, and deletions that predate authorization.
  - Verify only changes introduced after the baseline, or fail early when the baseline cannot be compared safely.
  - Keep feature worktrees optional rather than making them the correctness mechanism.
  - Design baseline metadata separately from Change Boundary v1 so authority projection does not become an operation log.
  - Add tests for pre-existing edits, concurrent unrelated changes, and clean operations.
  - Completion: unrelated dirty-worktree state cannot contaminate feature authority verification.

## P0 — Generated Codex skill exclusion

- [ ] Exclude generated `.agents/skills/speckit-*/**` materializations from implementation writes.
  - Centralize or reuse the generated-state classification instead of adding another isolated path rule where practical.
  - Preserve canonical `integration/` source as implementation state.
  - Add Git verification tests proving rematerialized Codex skills remain excluded.
  - Completion: supported bridge rematerialization cannot appear as an implementation authority write.

## P1 — Focused code and documentation cleanup

- [ ] Reduce duplication and split oversized project code or documentation into focused units.
  - Inventory project-controlled code and documentation above 250 lines.
  - Resolve or add explicit SpecDD ownership before editing any currently unowned artifact.
  - Split by stable responsibility rather than arbitrary line count.
  - Consolidate repeated JSON loading, output serialization, generated-state classification, and lifecycle wording where
    a shared abstraction improves clarity without coupling unrelated stages.
  - Keep README material introductory and delegate detailed lifecycle, development, and diagnostic behavior to focused
    guides.
  - Remove obsolete compatibility prose, duplicated workflow explanations, and dead helper code after tests protect the
    intended behavior.
  - Update `files.include` only when a file is genuinely generated, redundant, or irrelevant to future implementors.
  - Completion: project-controlled code and docs are focused, orthogonal, under 250 lines, and retain equivalent tested
    behavior.
