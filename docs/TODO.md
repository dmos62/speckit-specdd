# Implementation TODO

The P0 items below are derived from `docs/TECH-DEBT.md` and ordered for authority correctness. Completed items are
removed here: authorization preserves the validated Change Boundary in worktree Git metadata, records exact explicit
`.sdd` evolution targets, records explicitly selected editable bootstrap overrides, and rejects refresh-time boundaries
whose effective SpecDD governing context changed before authorization.

Boundary refresh now records deterministic per-target effective-context SHA-256 identities in refreshable current-
worktree Git metadata bound to the exact boundary. Authorization fresh-resolves the target context and rejects
ownership-preserving `Must`, `Forbids`, `References`, referenced-contract, governing-chain, or resolver-generation drift
with blocking `STALE_BOUNDARY`. The immutable authorization snapshot remains the historical post-authorization reference.

Pinned SpecDD CLI `1.1.1` requires resolver targets to exist. Until the CLI exposes resolver-backed intended-path
authority, the bridge retains non-existent implementation targets as `UNRESOLVED_TARGET` with an explicit
`INTENDED_TARGET_UNSUPPORTED` message and fails closed at task validation and authorization rather than inferring
pre-creation authority locally.

## P0 — Change Boundary semantic consistency

- [ ] Validate cross-field invariants before trusting a Change Boundary.
  - Require unique resolved target paths.
  - Require `authorities` to equal the distinct non-null target `primaryAuthority` values.
  - Require `crossBoundary` to agree with that authority set.
  - Prevent one path from appearing as both resolved and unresolved.
  - Validate candidate authorities and resolved spec relationships where deterministically knowable.
  - Decide whether nullable `primaryAuthority` remains a supported v1 representation or is removed.
  - Keep refresh-time context-evidence validation separate from boundary cross-field validation; it is fingerprint-bound
    generated metadata rather than part of Change Boundary v1.
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
  - Preserve the existing focused splits in `workflow_gate_state.py`, `validation_authority.py`, and
    `validation_permissions.py` unless later cleanup finds a clearer boundary.
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

## P2 — Intended-path resolver support

- [ ] Replace the current unsupported-creation fallback when SpecDD exposes resolver-backed intended-path authority.
  - Current pinned CLI `1.1.1` accepts only existing resolver targets; do not emulate missing-path resolution by parsing
    `.sdd` ownership locally or by creating temporary probe files in the worktree.
  - When an authoritative CLI/API query becomes available, cover exact ownership, existing-directory ownership, glob
    ownership, `Can modify`, ambiguous ownership, and no authority.
  - Preserve `.sdd` evolution-path exclusion from implementation boundaries.
  - Remove the `INTENDED_TARGET_UNSUPPORTED` fallback only after task-stage and authorization tests prove semantic parity
    with SpecDD intended-path rules.
