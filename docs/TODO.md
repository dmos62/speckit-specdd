# Implementation TODO

The P0 items below are derived from `docs/TECH-DEBT.md` and ordered for authority correctness. Completed items are
removed here: authorization preserves the validated Change Boundary in worktree Git metadata, records exact explicit
`.sdd` evolution targets, records explicitly selected editable bootstrap overrides, rejects refresh-time boundaries
whose effective SpecDD governing context changed before authorization, and records an operation-scoped Git baseline.

Boundary refresh records deterministic per-target effective-context SHA-256 identities in refreshable current-worktree
Git metadata bound to the exact boundary. Authorization fresh-resolves the target context and rejects ownership-
preserving `Must`, `Forbids`, `References`, referenced-contract, governing-chain, or resolver-generation drift with
blocking `STALE_BOUNDARY`. The immutable authorization snapshot remains the historical post-authorization reference.

Authorization also records the current Git `HEAD` plus exact content/deletion identities for every dirty path before
implementation. Verification excludes unchanged pre-authorization tracked, staged, untracked, and deleted state while
including any path whose state changed after authorization. A changed `HEAD` fails closed because the baseline can no
longer be compared safely; post-authorization concurrent writes remain in operation scope and should use an optional
isolated worktree when they must not participate in the same verification.

Pinned SpecDD CLI `1.1.1` requires resolver targets to exist. Until the CLI exposes resolver-backed intended-path
authority, the bridge retains non-existent implementation targets as `UNRESOLVED_TARGET` with an explicit
`INTENDED_TARGET_UNSUPPORTED` message and fails closed at task validation and authorization rather than inferring
pre-creation authority locally.

Change Boundary readers reject deterministic cross-field inconsistency before boundary state can influence
authorization or verification. Adapter-level tests separately establish that shape-valid corruption is rejected for
duplicate resolved targets, authority projection mismatch, owner/spec-chain mismatch, resolved/unresolved overlap, and
invalid candidate-authority state.

`docs/TECH-DEBT.md` still contains the completed operation-baseline risk because that file currently has no discoverable
SpecDD ownership or modification permission; do not edit it until ownership is made explicit.

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
