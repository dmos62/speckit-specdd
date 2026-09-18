# Technical Debt and Risk Register

This register contains unresolved bridge risks only.

Priorities:

- **P1**: can produce incorrect workflow behavior, incomplete semantic verification, false positives or negatives, or confusing operator outcomes.
- **P2**: maintainability, portability, integration robustness, and longer-term scaling concerns.

Completed authority-snapshot, effective-context freshness, semantic-consistency, bootstrap-control, Git-baseline, modification-permission, unplanned-specification, and generated-skill verification work is no longer listed as active debt.

## P1 — Workflow and semantic verification

- [ ] **Make semantic SpecDD contract verification an explicit workflow stage.**  
  Structural verification checks paths, historical authority evidence, control state, and `specdd lint`, but does not itself prove every applicable `Must`, `Must not`, `Forbids`, `Depends on`, `Scenario`, or `Done when` outcome. Add a deliberate agentic contract-verification stage with evidence or explicit uncertainty.

- [ ] **Do not imply stronger verification than the structural gate performs.**  
  `workflow_gate.py verify` invokes deterministic verification directly, while richer reasoning currently lives in the optional convergence layer. Align workflow wording and guarantees or introduce a required semantic review stage.

- [ ] **Define specification evolution as a first-class operation transition.**  
  Current semantics require specification evolution to finish before dependent implementation is freshly authorized. The workflow still presents one normal plan/tasks/authorize/implement sequence. Define the executable spec-only transition rather than relying only on guidance.

- [ ] **Support specification-only workflow operations deliberately.**  
  Task-stage structural validation currently requires an ordinary implementation target, while valid specification evolution may contain only `.sdd` targets. Provide an explicit validation and completion path for spec-only operations.

- [ ] **Unify active-feature discovery.**  
  Agent commands use the supported Spec Kit prerequisite script while structural gates use persisted or environment-provided feature state directly. Prefer one supported upstream feature-state interface so the mechanisms cannot diverge.

- [ ] **Verify extension hooks and workflow-overlay steps do not double-dispatch lifecycle stages.**  
  Both mechanisms register context, validation, authorization, and verification behavior. Add end-to-end evidence that one workflow invocation does not execute a bridge stage twice.

- [ ] **Define directory-target semantics.**  
  Planning may name directories while authorization and verification ultimately operate on concrete files. Either make directory targets advisory planning hints only or define deterministic descendant semantics without accidental broad authority.

- [ ] **Preserve Spec Kit task status during scope projection.**  
  Task parsing accepts checklist states but currently discards the marker. Define which pending, completed, skipped, blocked, and decision-needed tasks contribute to planning, validation, and authorization scope.

- [ ] **Make planning target extraction structured or explicitly conservative.**  
  Whole-document path extraction can interpret explanatory or read-only paths as candidate writes. Prefer an explicit plan section or supported upstream structured target metadata.

- [ ] **Harden task-path parsing without building an independent natural-language parser.**  
  Exact-path heuristics can miss unusual filenames or capture path-looking prose. Prefer structured upstream task metadata when available.

- [ ] **Require deliberate handling of `MULTI_AUTHORITY_TASK` warnings.**  
  Legitimate multi-owner work must remain possible, but naturally decomposable tasks can currently proceed without a recorded architectural decision. Add acknowledgement or review without converting the warning into automatic failure.

- [ ] **Align diagnostic severity, summary blocking state, process exit behavior, and user-facing acceptance semantics.**  
  Define one predictable contract for whether each diagnostic blocks acceptance, fails a workflow gate, or merely requires review.

- [ ] **Keep the meaning of authorization narrow and explicit.**  
  Deterministic authorization proves trusted scope, fresh governing context, and applicable write authority. It does not prove complete semantic conformance with every behavioral SpecDD rule. User-facing wording should preserve that distinction.

- [ ] **Ensure direct task-command execution refreshes context before validation.**  
  The structural workflow refreshes the boundary after tasks, while direct command behavior still depends partly on preset instructions. Make direct execution deterministic.

## P2 — Semantic parity and maintainability

- [ ] **Replace local ownership-path interpretation when SpecDD exposes authoritative target ownership APIs.**  
  The bridge uses real resolver output but still evaluates returned `Owns` and `Can modify` path entries locally. Prefer resolver/API output that directly reports ownership and modification authority.

- [ ] **Replace or tightly bound the custom JSON Schema subset.**  
  The current validator supports only the keywords required by Change Boundary v1. Use a maintained validator or keep the supported subset explicitly constrained and covered.

- [ ] **Centralize generated-state classification further where one source can serve bootstrap, verification, and documentation.**  
  Verification now correctly excludes generated Codex skill materializations, but generated-state knowledge still appears in several project surfaces.

- [ ] **Harden SpecDD CLI version discovery.**  
  Version detection depends on executable layout and npm global metadata. Prefer an authoritative machine-readable CLI version command when available.

- [ ] **Define and test the supported host matrix.**  
  Current evidence is Windows with a Bash-capable environment, PowerShell-based Spec Kit prerequisites, and POSIX-shell workflow gates. Establish intentional Windows, Linux, and macOS expectations before platform assumptions spread.

- [ ] **Add non-ASCII path coverage.**  
  Exercise Unicode repository paths through Git porcelain, normalization, resolver calls, boundary generation, and verification on supported hosts.

- [ ] **Define transport for historical authorization evidence across CI jobs or machines.**  
  Authorization evidence is current-worktree Git metadata. Distributed execution needs an explicit artifact-transfer model that preserves the exact historical snapshot, companion plan, and baseline.

- [ ] **Add an end-to-end test through the real resolved Spec Kit workflow.**  
  Current tests cover components, installation, and workflow resolution. A disposable repository should exercise the actual workflow through planning, tasks, authorization, implementation change, and verification.

- [ ] **Add invocation-count coverage for hook and overlay interaction.**  
  Installation proves both mechanisms exist but not whether the same lifecycle stage can execute twice.

- [ ] **Expand explicit `Can modify` integration coverage as authority scenarios evolve.**  
  Preserve tests for permitted non-owning modification and denial without a grant as resolver behavior or task metadata changes.

- [ ] **Add intended new-file authorization coverage when SpecDD exposes resolver-backed intended-path authority.**  
  Cover exact ownership, directory ownership, glob ownership, `Can modify`, ambiguous ownership, and absent authority without local emulation.

- [ ] **Add explicit directory-target coverage if directory targets remain supported.**

- [ ] **Add skipped and blocked task-state coverage after task-state semantics are defined.**

- [ ] **Resolve the nullable `primaryAuthority` compatibility state before Change Boundary v2.**  
  Generation normally represents unknown authority in `unresolved`; decide whether nullable authority remains a supported external v1 compatibility form.

- [ ] **Define Change Boundary schema-version compatibility before introducing v2.**  
  Specify whether older historical snapshots are rejected, migrated, or supported concurrently.

- [ ] **Distinguish repository-wide lint failure from operation-introduced lint failure.**  
  `specdd lint` may fail because of unrelated pre-existing state. Future verification should distinguish baseline debt from violations introduced by the active operation.

- [ ] **Surface application-test evidence separately from SpecDD lint.**  
  Feature correctness remains a Spec Kit concern, but final workflow reporting should make required behavioral-test execution visible.

- [ ] **Require at least one acceptance environment with all external tools installed.**  
  Tests that skip when SpecDD, Spec Kit, or Git is unavailable must not allow CI to pass without exercising the real pinned toolchain.

- [ ] **Keep optional dedicated worktrees as an isolation mechanism, not an authority primitive.**  
  Historical baselines remain the correctness mechanism; worktrees may reduce concurrent noise without changing SpecDD semantics.
