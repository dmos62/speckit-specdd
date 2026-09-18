# Technical Debt and Risk Register

This file tracks known correctness gaps, lifecycle ambiguities, implementation risks, and hardening work for the Spec Kit × SpecDD bridge.

Priorities:

- **P0**: can weaken authority guarantees, misclassify permitted work, or allow an implementation operation to be verified against the wrong authority context.
- **P1**: can produce incorrect workflow behavior, incomplete semantic verification, false positives/negatives, or confusing operator outcomes.
- **P2**: maintainability, portability, integration robustness, and longer-term scaling concerns.

## P0 — Authority and correctness

- [ ] **Preserve an immutable authorization snapshot across specification evolution.**
  `boundary.json` is currently both refreshable feature context and the authority snapshot used by authorization and verification. An evolution task can refresh it during implementation, replacing the historical snapshot that verification is supposed to compare against. Define an operation boundary that prevents dependent implementation from continuing under a refreshed boundary in the same authorized operation, or retain a separate immutable authorization snapshot.

- [ ] **Support intended non-existent implementation targets without treating all creation as unresolved authority.**
  `build_change_boundary()` currently emits `UNRESOLVED_TARGET` before invoking SpecDD when a target does not exist. SpecDD permits intended ordinary files when their pre-operation path is covered by applicable `Owns` or `Can modify` authority. Either add resolver-backed intended-path resolution or explicitly declare new implementation-file creation unsupported until the SpecDD CLI exposes the required authority query.

- [ ] **Model modification permission separately from primary ownership.**
  The bridge derives a target's primary authority from `Owns`, but does not project `Can modify` or otherwise establish which active authority is permitted to perform a cross-owned write. A task can currently contain targets from several owners and receive only `MULTI_AUTHORITY_TASK`. Define how task/operation authority relates to SpecDD `Owns` plus `Can modify`, and deterministically reject writes that are owned but not permitted for the operation when that distinction is applicable.

- [ ] **Do not treat arbitrary changed `.sdd` files as merely informational.**
  Verification currently reports all changed `.sdd` files as `SPEC_EVOLUTION_PRESENT` with informational severity. It does not prove that those specification files were explicitly selected by an evolution task or authorized SpecDD workflow. Compare actual changed specifications with explicit planned evolution targets so silent or accidental spec edits are surfaced as a failure or mandatory review condition.

- [ ] **Enforce bootstrap control-file authority during verification.**
  Any changed root `.specdd/` control file is currently reported as `CONTROL_STATE_CHANGED` with warning severity. This includes immutable `.specdd/bootstrap.md` and `.specdd/bootstrap.project.md`, whose edits require explicit authority under the bootstrap contract. Classify immutable or unplanned control changes separately and block them when the SpecDD control-file rules require it.

- [ ] **Detect SpecDD contract changes between boundary generation and authorization.**
  `STALE_BOUNDARY` currently detects feature identity and task-path drift, but not changes to governing `.sdd` content when the target paths stay the same. A boundary can therefore be authorized after its owning spec, inherited constraints, references, or authority rules changed. Record and validate a stable fingerprint or equivalent generation identity for the effective SpecDD state used to create the boundary.

- [ ] **Validate semantic consistency of loaded Change Boundary documents.**
  JSON Schema validation does not establish that `authorities` equals the set of target `primaryAuthority` values, that target paths are unique, that unresolved and resolved entries do not conflict, or that authority data is internally coherent. A manually altered or corrupted `boundary.json` can satisfy the schema while changing authorization behavior. Add deterministic cross-field invariants before authorization and verification trust a boundary.

- [ ] **Bind verification to one implementation operation rather than the entire dirty worktree.**
  `collect_git_changes()` treats all current Git changes as belonging to the active feature. Pre-existing edits, concurrent feature work, editor-generated changes, or another agent's modifications can cause false drift/authority failures or contaminate the operation. Record an authorization-time Git baseline or require an isolated clean execution context. Dedicated feature worktrees are a useful optional isolation mechanism but should not be the only correctness mechanism.

- [ ] **Exclude generated Codex skill materializations from implementation writes.**
  Documentation and `files.include` treat `.agents/skills/speckit-*/**` as generated state, but `verification_git.py` does not exclude `.agents/skills/`. Rematerialized commands can therefore be interpreted as implementation writes and subjected to SpecDD authority checks.

## P1 — Workflow and semantic verification

- [ ] **Make semantic SpecDD contract verification an explicit workflow stage.**
  The bootstrap requires implementing agents to check applicable `Must`, `Must not`, `Forbids`, `Depends on`, `Scenario`, and `Done when` entries, but the structural post-implementation gate checks primarily paths, authority, and `specdd lint`. Add an explicit agentic contract-verification pass over the effective specs for actual changed targets and report evidence or uncertainty for material rules.

- [ ] **Do not let the structural workflow imply stronger verification than it performs.**
  `workflow_gate.py verify` calls deterministic `verification.py` directly and therefore bypasses the agentic reasoning described by `commands/verify.md`. The normal `speckit` workflow ends after this deterministic shell gate; `speckit.converge` is optional. Clarify the guarantee or add a workflow stage that performs the agentic system-contract review.

- [ ] **Define specification evolution as an operational lifecycle transition.**
  Current task guidance allows evolution tasks followed by a context refresh before dependent implementation, while the workflow has one authorization gate followed by one implementation step. Define how a spec-only operation ends, how a new boundary is created, and how dependent implementation is re-authorized. Authority evolution in particular must end the old operation rather than mutate its authority mid-run.

- [ ] **Support specification-only workflow operations deliberately.**
  The task-stage structural gate requires at least one non-`.sdd` target, while the design requires specification evolution to be separate from implementation. A legitimate operation containing only deliberate `.sdd` evolution should have a defined validation and completion path rather than failing because no implementation boundary exists.

- [ ] **Unify active-feature discovery between agent commands and structural gates.**
  Command instructions use Spec Kit's PowerShell prerequisite script to discover `FEATURE_DIR`, while `workflow_gate.py` reads `SPECIFY_FEATURE_DIRECTORY` or `.specify/feature.json` directly. These mechanisms can disagree or change independently. Use one supported Spec Kit feature-state interface where possible.

- [ ] **Verify hook and workflow-overlay interaction does not duplicate lifecycle execution.**
  The extension declares `after_plan`, `after_tasks`, `before_implement`, and `after_implement` hooks while the workflow overlay independently inserts equivalent structural steps. Confirm whether the Spec Kit workflow engine also dispatches those hooks for its command steps. Prevent duplicate boundary refreshes, validation, authorization, verification, resolver calls, and lint runs.

- [ ] **Define directory-target semantics.**
  Context and task documentation permits file or directory targets, but verification compares actual file writes with planned target paths. A planned directory does not currently establish whether descendants are planned, producing ambiguous behavior. Either make directory targets planning-only hints that must become files before authorization, or define exact subtree semantics without turning directory paths into accidental broad globs.

- [ ] **Preserve and use Spec Kit task status during scope projection.**
  `parse_tasks()` accepts all supported checklist states but `TaskRecord` discards the marker. Skipped, blocked, completed, and pending tasks therefore contribute equally to the refreshed boundary and authority set. This can widen the planned authority domains with work that will not execute. Preserve task state and define which states participate in each lifecycle stage.

- [ ] **Make planning target extraction context-aware or explicitly conservative.**
  `_plan_targets()` runs repository-path extraction over the entire `plan.md`. Any path-looking text can become a candidate even when it is documentation, an example, an existing read-only dependency, or explanatory prose. Restrict extraction to an explicit plan section/structure or introduce structured target metadata when Spec Kit provides a supported mechanism.

- [ ] **Harden task-path parsing without growing an independent NLP layer.**
  `validation_tasks.py` uses regular expressions over Markdown prose. It can miss unusual valid filenames and can interpret path-looking prose as intended writes. Keep exact-path requirements, but prefer structured upstream task metadata when available rather than continuously expanding heuristic parsing.

- [ ] **Require meaningful review of `MULTI_AUTHORITY_TASK` warnings.**
  The structural task gate allows warnings to pass, and there is no mandatory review gate between task validation and authorization. Legitimate cross-domain work must remain possible, but naturally decomposable multi-authority tasks can currently proceed without any agentic decision being recorded. Add a review mechanism or explicit acknowledgement when architectural interpretation is required.

- [ ] **Align diagnostic severity, `summary.blocking`, process exit behavior, and user-facing acceptance semantics.**
  `SPECDD_DRIFT` is an `error` but does not set `summary.blocking`; the structural workflow nevertheless fails because it uses `--fail-on error`. Direct command guidance focuses on `summary.blocking`. Define one predictable contract for whether a finding blocks acceptance, fails a workflow step, or merely requires review.

- [ ] **Clarify the meaning of “authorize”.**
  Current deterministic authorization proves that task targets are represented by a trustworthy ownership projection and are not stale/unresolved. It does not generally prove semantic compliance with `Must`, `Must not`, `Forbids`, or every `Can modify` relationship. Document the narrower guarantee or extend the checks so “authorized” cannot be mistaken for complete SpecDD conformance.

- [ ] **Verify direct `/speckit.tasks` execution refreshes context reliably before its validation hook.**
  The `after_tasks` extension hook invokes validation, which does not refresh the boundary. The preset augmentation instructs the agent to run context during task generation, while the structural workflow refreshes deterministically after tasks. Direct task-command execution is therefore dependent on the agent following augmentation instructions and may validate against a stale planning boundary.

- [ ] **Track governing-spec-chain drift even when ownership is unchanged.**
  `resolvedSpecs` is stored in the boundary but verification primarily compares target authority. A parent/local/reference spec can change or enter/leave the effective chain while primary ownership remains identical. This can materially alter `Must`, `Forbids`, dependencies, or scenarios without producing deterministic boundary drift. Include effective-context identity in staleness checks.

## P2 — Semantic parity and maintainability

- [ ] **Reduce local reimplementation of SpecDD ownership semantics.**
  The adapter calls the real `specdd resolve`, but then locally parses `Owns`, resolves SpecDD paths, implements glob behavior, and determines ownership in `boundary_specdd.py` and `boundary_paths.py`. This creates semantic-drift risk when SpecDD evolves. Prefer a SpecDD CLI/API operation that directly returns authoritative owner/modification information for a target.

- [ ] **Remove or minimize the custom JSON Schema implementation.**
  `boundary_schema_validation.py` implements a selected subset of JSON Schema Draft 2020-12. Future schema changes can silently exceed the supported keyword subset or diverge from standard validator semantics. Either use a maintained JSON Schema implementation or strictly test and document the intentionally supported schema subset.

- [ ] **Centralize generated-state classification.**
  Generated/canonical path knowledge is duplicated across `files.include`, documentation, bootstrap checks, and `verification_git.py`. The missing `.agents/skills/` exclusion demonstrates the drift risk. Define one canonical generated-state policy consumable by verification and tests where practical.

- [ ] **Harden SpecDD CLI version discovery.**
  `specdd_cli_version()` depends on executable layout assumptions and npm global package metadata. Alternative npm prefixes, shims, package managers, or future CLI packaging can make a valid installation unverifiable. Prefer an authoritative machine-readable CLI version command once available.

- [ ] **Clarify host portability requirements and test them intentionally.**
  The current evidence baseline is Windows 10 under a Bash-capable environment, while direct bridge commands require PowerShell and workflow overlay commands use POSIX shell syntax such as `command -v`. Other operating systems are explicitly unverified. Establish the intended host matrix before accidental platform assumptions become entrenched.

- [ ] **Add non-ASCII path coverage for Git and resolver integration.**
  Git porcelain is consumed with Python text decoding based on the host environment. Existing tests cover spaces and grouping characters but not Unicode filenames. Add tests for non-ASCII paths on supported hosts and normalize subprocess encoding behavior if necessary.

- [ ] **Define distributed/CI transport for the historical authority snapshot.**
  `boundary.json` is intentionally ignored and rebuildable, but verification requires the exact planned snapshot rather than a freshly regenerated one. Authorization and verification occurring in different processes, machines, containers, or CI jobs therefore need an explicit snapshot artifact-transfer model.

- [ ] **Add an end-to-end test through the real resolved Spec Kit workflow.**
  Current tests cover source, command installation, overlay resolution, gate functions, fixture resolution, and individual validation/verification components. Add a disposable-repository acceptance test that runs the actual `speckit` workflow through planning, tasks, structural gates, implementation changes, and verification to catch integration behavior that unit/source tests cannot expose.

- [ ] **Add tests for hook/overlay double-dispatch behavior.**
  Installation tests prove hooks and overlay steps both exist, but not whether one workflow invocation causes both mechanisms to execute the same bridge stage. Capture invocation counts or observable state in a disposable integration test.

- [ ] **Add tests for unplanned specification and bootstrap-control changes.**
  Verification tests prove specification changes cannot retroactively authorize a new implementation domain, but they do not establish that an unexpected `.sdd` edit or immutable bootstrap edit is rejected as an unauthorized change in its own right.

- [ ] **Add tests for `Can modify` scenarios.**
  The fixture contains separate owners and a forbidden dependency but does not exercise a legitimate non-owning modification permission. Add fixture cases where one spec may modify a path owned by another spec and where the same write is denied without that grant.

- [ ] **Add tests for intended new-file authorization.**
  Once intended-path resolution is defined, cover creation under exact ownership, directory ownership, glob ownership, `Can modify`, ambiguous ownership, and no authority.

- [ ] **Add tests for directory targets or explicitly reject them.**
  Ensure planning, task validation, authorization, and verification all agree on whether a directory is a valid implementation target and what descendant writes it represents.

- [ ] **Add tests for skipped and blocked task states.**
  Verify that `[-]`, `[!]`, `[?]`, `[x]`, and open tasks affect boundary construction and authorization according to the intended lifecycle rather than all widening scope identically.

- [ ] **Add semantic consistency checks to schema tests.**
  Current schema tests validate shape and selected cross-boundary constraints but not the relationship between targets, authorities, unresolved records, and governing specs. Add adapter-level invariant tests even if these relationships cannot be expressed conveniently in JSON Schema.

- [ ] **Resolve the nullable `primaryAuthority` schema state.**
  The schema permits resolved targets with `primaryAuthority: null`, while the current builder classifies inability to derive one authority into `unresolved` instead. Decide whether nullable authority is a supported v1 state or remove the unused representation to avoid multiple ways to encode the same condition.

- [ ] **Define Change Boundary schema-version compatibility behavior.**
  The schema is fixed at version `1`, but readers do not currently expose an explicit migration/rejection strategy beyond schema validation. Before schema v2 exists, define whether old snapshots are rejected, migrated, or supported concurrently.

- [ ] **Distinguish repository-wide SpecDD lint failure from operation-introduced lint failure.**
  Verification runs `specdd lint` over the resulting repository. Pre-existing unrelated lint failures can block the active feature even if the operation did not introduce them. An operation baseline or clean-worktree requirement should make this deterministic, or verification should report baseline versus newly introduced violations separately.

- [ ] **Surface project-test evidence separately from SpecDD lint.**
  `specdd-verify` records SpecDD lint but does not consume or record application test results. Feature correctness remains Spec Kit's responsibility, but the final workflow should make it clear whether behavioral tests required by relevant scenarios or project governance actually ran.

- [ ] **Avoid allowing skipped external-tool integration tests to create false confidence.**
  Several real fixture and install tests skip when `specdd`, `specify`, or Git is unavailable. Ensure CI/acceptance has at least one mandatory environment where those tools are installed at the pinned versions so the integration suite cannot pass solely on unit tests.

- [ ] **Document or automate clean-worktree expectations when operation baselines are absent.**
  Until operation-scoped Git baselines exist, successful authority verification assumes the dirty worktree represents one feature operation. Make that precondition explicit and fail early when a clean starting state is required.

- [ ] **Consider optional dedicated Git worktrees for concurrent feature execution.**
  A feature-specific worktree can isolate active Spec Kit state, derived boundaries, uncommitted implementation writes, and parallel agents. Keep this optional rather than making Git worktrees part of SpecDD semantics, and still retain planned-versus-actual verification inside each worktree.