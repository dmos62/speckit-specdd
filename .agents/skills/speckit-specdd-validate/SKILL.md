---
name: speckit-specdd-validate
description: Validate the active feature's Spec Kit tasks against the current SpecDD Change Boundary.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: SpecDD contributors
  source: specdd:commands/validate.md
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input before validation. The optional lifecycle stage may be `planning`, `tasks`, or
`implementation`. Default to `tasks`.

## Goal

Validate concrete Spec Kit task write targets against the active feature's derived SpecDD Change Boundary. Deterministic
path, ownership, and modification-permission mechanics belong to the bridge validation scripts. Architectural
classification remains an agentic responsibility where the deterministic result cannot decide intent.

The Change Boundary preserves target ownership through `primaryAuthority`. Unmarked tasks use their target owners as
participating operation authorities. A task that intentionally executes all writes under one authority declares the
literal `SPECDD_AUTHORITY:` followed by a backticked repository-relative `.sdd` path. Validation then fresh-resolves that
authority context and projects inherited `Can modify` grants. A non-owning grant never changes the target owner.

This command never rewrites tasks, edits `.sdd` files, relaxes SpecDD authority, or creates implementation authorization.

## External dependency failures

If a required external command is missing or cannot start (`pwsh` for prerequisite discovery, `git`, `uv`, or `specdd`
when reached), report it as an infrastructure failure and stop. Preserve the tool error, direct the user to
`bash .specify/extensions/specdd/scripts/bootstrap.sh --check`, and do not convert tool absence into unresolved-target, stale-boundary, or authority
diagnostics.

## Execution

1. From the repository root, run:

       .specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly

   Parse `FEATURE_DIR` from the JSON result. If the command fails or no active feature is available, stop and instruct
   the user to create or select a feature with `/speckit.specify`.

2. Resolve the repository root with:

       git rev-parse --show-toplevel

   Treat that path as the bridge root. `FEATURE_DIR` must resolve inside it. Stop if the active feature is outside the
   repository root.

3. Derive:
   - `FEATURE_ID` as the basename of `FEATURE_DIR`.
   - `BOUNDARY_FILE` as `FEATURE_DIR/.specdd/boundary.json`.
   - `TASK_FILE` as `FEATURE_DIR/tasks.md`.

4. Require both current inputs:
   - If `BOUNDARY_FILE` does not exist, stop and instruct the user to run `/speckit.specdd.context`.
   - If `TASK_FILE` does not exist, stop and instruct the user to generate tasks with `/speckit.tasks`.

5. Select validation strictness:
   - `planning`: unresolved or invalid declared-authority scope is advisory while implementation paths may still be
     emerging.
   - `tasks`: unresolved, stale, or invalid declared-authority scope is an error that must be corrected before
     implementation planning is considered complete.
   - `implementation`: stale scope blocks, and unknown, conflicting, or unpermitted write authority produces a blocking
     `AUTHORITY_VIOLATION`.
   - If `$ARGUMENTS` does not select a stage, use `tasks`.

6. Run the deterministic validator:

       uv run --no-project python integration/specdd/scripts/validation.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --boundary "<feature-dir>/.specdd/boundary.json" \
         --tasks "<feature-dir>/tasks.md" \
         --stage "<stage>"

   Do not parse `.sdd` source, derive ownership independently, or repair the Change Boundary by hand. When task text
   contains `SPECDD_AUTHORITY:`, the validator calls the real SpecDD resolver for that authority context and evaluates
   `Can modify` from resolver output.

7. Interpret deterministic diagnostics:
   - `UNRESOLVED_TARGET`: a boundary or task target does not currently have trustworthy authority projection.
   - `INTENDED_TARGET_UNSUPPORTED`: the active SpecDD resolver lacks the complete `--file`, `--folder`, and `--sdd-file`
     transport needed to resolve that missing target before creation. This is a resolver-capability limitation rather
     than evidence that SpecDD forbids creation.
   - `MULTI_AUTHORITY_TASK`: one task writes targets owned by more than one primary authority. This remains a structural
     finding and does not by itself imply invalidity.
   - `AUTHORITY_VIOLATION`: at task or implementation strictness, a declared `SPECDD_AUTHORITY:` is invalid, conflicting,
     or lacks `Owns`/`Can modify` coverage for every resolved write target; implementation strictness also uses this code
     for unresolved or conflicting target authority.
   - `STALE_BOUNDARY`: current task targets or feature identity no longer match the boundary projection.
   - `EVOLUTION_CLASSIFICATION_CONFLICT`: a task declares both supported evolution classes and must be corrected.
   - `EVOLUTION_SPEC_TARGET_REQUIRED`: an evolution task does not name a `.sdd` target.
   - `EVOLUTION_SCOPE_MIXED`: an evolution task mixes `.sdd` evolution with ordinary implementation writes instead of
     keeping the operations separate.

   `modificationPermissions` reports each target's owner, the task authorities permitted to write it, and the resolved
   spec sources of non-owning `Can modify` grants. Ownership remains unchanged.

8. Preserve Spec Kit task identity:
   - Keep original task order.
   - Keep the original task ID as the anchor when discussing decomposition.
   - Keep the original user-story grouping.
   - Do not rewrite `tasks.md` automatically.
   - For genuinely coordinated multi-owner work, an absent `SPECDD_AUTHORITY:` is valid and `operationAuthorities`
     reflects the participating owners.
   - When a declared authority cannot cover cross-owned targets, recommend removing an unnecessary declaration,
     decomposing by `authorityGroups`, or correcting the implementation path instead of relaxing authority.

9. Apply architectural classification only where reasoning is required:
   - Use `IMPLEMENTATION_CONFLICT` when the requested feature can remain unchanged but the proposed task structure or
     write path conflicts with current SpecDD boundaries.
   - Use `SPEC_EVOLUTION_REQUIRED` when the requested behavior genuinely requires a durable system-contract change.
   - Use `AUTHORITY_EVOLUTION_REQUIRED` when the requested behavior genuinely requires persistent ownership or write
     permission to change.
   - Explicit evolution tasks use `SPEC_EVOLUTION_REQUIRED:` or `AUTHORITY_EVOLUTION_REQUIRED:` in ordinary task text,
     not a custom checklist marker. The validator projects that intent into the task `classification` and `evolution`
     fields without treating it as authority.
   - A task merely touching multiple owners is not sufficient evidence for spec or authority evolution.

10. For each deliberate evolution classification, include a compact Proposed `.sdd` delta subsection in the command
    response:
    - Name the exact target `.sdd` file or files.
    - Describe the smallest affected sections and entries needed for the durable contract.
    - Keep the proposal advisory and concise; do not duplicate unrelated inherited rules.
    - Do not apply the proposed delta from this command.
    - State that the proposal is not authority for the current operation.

11. Enforce the authority-snapshot invariant:
    - Never treat a proposed or newly edited `.sdd` file as authority for the current implementation operation.
    - The validator's evolution projection sets `requiresFreshBoundary` for deliberate spec evolution.
    - `AUTHORITY_EVOLUTION_REQUIRED` also sets `endsAuthorityContext`; after that specification operation is applied,
      the current authority context is over.
    - Apply specification evolution separately, then run `/speckit.specdd.context`.
    - Before dependent implementation begins, run `/speckit.specdd.authorize` to establish a new immutable authorization
      snapshot from the refreshed Change Boundary.

## Output

Report, in task order: stage, task identity, write targets, owner domains, declared `SPECDD_AUTHORITY:` when present,
`operationAuthorities`, `modificationPermissions`, deterministic classification, evolution projection, diagnostics, and
authority-local decomposition guidance when useful.

If any blocking diagnostic exists, state that implementation must not proceed under the current boundary. Keep
deterministic findings distinct from architectural interpretation.

## Constraints

- Never edit `.sdd` files.
- Never rewrite Spec Kit tasks automatically.
- Never synchronize Spec Kit task markers with SpecDD `Tasks:` entries.
- Never infer ownership or non-owning modification permission from descriptive task wording, directory names, proximity,
  or non-existent target ownership patterns; only the explicit `SPECDD_AUTHORITY:` marker selects a non-owning task
  authority.
- Never relax SpecDD ownership or write authority to make a task valid.