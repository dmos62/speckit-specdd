---
name: speckit-specdd-context
description: Build or refresh the active feature's derived SpecDD Change Boundary.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: SpecDD contributors
  source: specdd:commands/context.md
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input before discovery. Explicit target paths supplied by the user take precedence over
targets discovered from feature artifacts.

## Goal

Project the current feature's concrete or intended non-spec implementation write targets onto SpecDD authority by
calling the existing Change Boundary adapter. This command creates derived state only. It does not edit `.sdd` files,
infer ownership itself, relax authority, or treat root `.specdd/` bootstrap controls as implementation targets.

Each successful refresh also records deterministic effective-SpecDD context fingerprints in current-worktree Git
metadata. That refreshable evidence is bound to the exact generated Change Boundary and lets authorization detect
governing contract drift without copying persistent rule text into `boundary.json`.

Pinned SpecDD CLI `1.1.1` requires resolver targets to exist. The adapter therefore retains a non-existent intended
target as `UNRESOLVED_TARGET` with an `INTENDED_TARGET_UNSUPPORTED` message instead of locally inventing pre-creation
authority. This is a bridge limitation, not a statement that SpecDD forbids creating the file.

## External dependency failures

If a required external command is missing or cannot start (`pwsh` for prerequisite discovery, `git`, `uv`, or `specdd`
when reached), report it as an infrastructure failure and stop. Preserve the tool error, direct the user to
`bash .specify/extensions/specdd/scripts/bootstrap.sh --check`, and do not convert tool absence into unresolved-target or authority diagnostics.

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

4. Discover candidate targets in this order:
   - If `$ARGUMENTS` contains explicit repository file or directory paths, use those ordinary non-`.sdd`,
     non-bootstrap-control implementation targets and do not add discovered targets.
   - Otherwise, if `FEATURE_DIR/tasks.md` exists, collect exact ordinary implementation paths named by task
     descriptions as files to create or modify.
   - If tasks produced no targets and `FEATURE_DIR/plan.md` exists, collect exact ordinary source paths named in the
     project structure or as concrete files/directories to create or modify.
   - Ignore `.sdd` paths during Change Boundary discovery. They are specification-evolution targets, not ordinary
     project write targets, and do not grant implementation authority.
   - Ignore root `.specdd/` bootstrap control paths during Change Boundary discovery. Their edit authority is enforced
     separately by authorization and verification.
   - Do not derive targets from symbols, URLs, libraries, headings, similar filenames, or semantic guesses.
   - Keep intended ordinary paths even when they do not exist yet. Under pinned SpecDD CLI `1.1.1`, the adapter retains
     them as unresolved with an `INTENDED_TARGET_UNSUPPORTED` message because `specdd resolve` cannot authorize a
     missing target.
   - Preserve first-seen order while removing exact duplicate path strings.

5. If no candidate target exists:
   - Remove `BOUNDARY_FILE` if it exists so stale derived state is not presented as current.
   - Report that the active feature does not yet name a concrete or intended ordinary implementation target.
   - Report that planning, deliberate spec evolution, or explicitly selected bootstrap-override work can continue, but
     an implementation Change Boundary cannot be generated until at least one ordinary implementation target is known.
   - Stop without creating a replacement boundary.

6. Run the existing adapter once with all discovered targets:

       uv run --no-project python integration/specdd/scripts/boundary.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --output "<feature-dir>/.specdd/boundary.json" \
         --record-context-evidence \
         <targets...>

   Quote each path independently. Do not parse `.sdd` files or reproduce resolver logic in this command.

7. The adapter fingerprints the normalized resolver-returned effective spec context for each resolved target, including
   inherited and explicit-reference context returned by `specdd resolve --sections all`. It stores those hashes in
   refreshable current-worktree Git metadata bound to the exact Change Boundary. It does not copy rule text into the
   feature artifact.

8. If the adapter exits nonzero:
   - Treat the run as failed.
   - Do not synthesize or repair `boundary.json` by hand.
   - Report the adapter error and leave any previous file untouched unless step 5 removed it because no targets existed.

9. Load the newly written `BOUNDARY_FILE` and report:
   - output path,
   - resolved target count,
   - authority domains,
   - `crossBoundary`,
   - unresolved entries grouped by diagnostic `code`,
   - that effective SpecDD context evidence was recorded successfully.

   Distinguish:
   - `INVALID_TARGET`: input cannot identify a repository target.
   - `UNRESOLVED_TARGET`: valid input cannot currently resolve to one primary authority.
   - `RESOLUTION_FAILED`: SpecDD resolver execution or output failed.
   - `AMBIGUOUS_AUTHORITY`: multiple resolved specs claim ownership.

10. Treat unresolved entries as incomplete context, not permission.

## Output

Keep the result compact. Include the boundary path, targets, authorities, cross-boundary status, unresolved diagnostics,
and context-evidence status. When the feature has no ordinary implementation target yet, state that no current boundary
exists.

## Constraints

- Never edit `.sdd` files.
- Never include `.sdd` evolution targets as implementation authority targets.
- Never include root `.specdd/` bootstrap controls as implementation authority targets.
- Never patch `.specify/`, `.specify-agent/`, or root `.specdd/` framework files to expose this command.
- Never duplicate persistent SpecDD constraints into feature artifacts or fingerprint metadata.
- Never infer write authority from proximity, naming, task grouping, or a missing intended path.