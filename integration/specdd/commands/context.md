---
description: Build or refresh the active feature's derived SpecDD Change Boundary.
---

## User Input

User input: `$ARGUMENTS`

You **MUST** consider user input before discovery. Explicit target paths supplied by the user take precedence over
targets discovered from feature artifacts.

## Goal

Project the current feature's concrete or intended write targets onto SpecDD authority by calling the existing Change
Boundary adapter. This command creates derived state only. It does not edit `.sdd` files, infer ownership itself, or
relax authority.

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
   - If `$ARGUMENTS` contains explicit repository file or directory paths, use those targets and do not add discovered
     targets.
   - Otherwise, if `FEATURE_DIR/tasks.md` exists, collect the exact file or directory paths named by task descriptions
     as files to create or modify.
   - If tasks produced no targets and `FEATURE_DIR/plan.md` exists, collect exact source paths named in the project
     structure or as concrete files/directories to create or modify.
   - Do not derive targets from symbols, URLs, libraries, headings, similar filenames, or semantic guesses.
   - Keep intended paths even when they do not exist yet; the adapter must classify them as unresolved rather than the
     command silently dropping them.
   - Preserve first-seen order while removing exact duplicate path strings.

5. If no candidate target exists:
   - Remove `BOUNDARY_FILE` if it exists so stale derived state is not presented as current.
   - Report that the active feature does not yet name a concrete or intended target.
   - Report that planning can continue, but a Change Boundary cannot be generated until at least one target is known.
   - Stop without creating a replacement boundary.

6. Run the existing adapter once with all discovered targets:

       uv run --no-project python integration/specdd/scripts/boundary.py \
         --root "<repository-root>" \
         --feature "<feature-id>" \
         --output "<feature-dir>/.specdd/boundary.json" \
         <targets...>

   Quote each path independently. Do not parse `.sdd` files or reproduce resolver logic in this command. Let the adapter
   normalize targets, call `specdd resolve`, derive primary authority, validate the schema, and atomically replace the
   prior derived file.

7. If the adapter exits nonzero:
   - Treat the run as failed.
   - Do not synthesize or repair `boundary.json` by hand.
   - Report the adapter error and leave any previous file untouched unless step 5 removed it because no targets existed.

8. Load the newly written `BOUNDARY_FILE` and report:
   - output path,
   - resolved target count,
   - authority domains,
   - `crossBoundary`,
   - unresolved entries grouped by diagnostic `code`.

   Distinguish these unresolved classes explicitly:
   - `INVALID_TARGET`: input cannot identify a repository target.
   - `UNRESOLVED_TARGET`: path is valid as input but cannot currently resolve to one primary authority.
   - `RESOLUTION_FAILED`: SpecDD resolver execution or output failed.
   - `AMBIGUOUS_AUTHORITY`: multiple resolved specs claim ownership.

9. Treat unresolved entries as incomplete context, not permission. Do not convert them into authority. Validation and
   implementation gates decide whether unresolved context is acceptable at later lifecycle stages.

## Output

Keep the result compact. Include the boundary path, targets, authorities, cross-boundary status, and unresolved
diagnostics. When the feature has no target yet, state that no current boundary exists.

## Maintainer Smoke Test

This smoke test exercises the same adapter path used by the command without installing the extension. Run it from the
repository root when changing this command or the adapter:

    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "$tmp_dir"' EXIT
    uv run --no-project python integration/specdd/scripts/boundary.py \
      --root tests/fixtures/specdd-two-domain \
      --feature context-smoke \
      --output "$tmp_dir/first.json" \
      src/auth/service.ts src/users/repository.ts
    uv run --no-project python integration/specdd/scripts/boundary.py \
      --root tests/fixtures/specdd-two-domain \
      --feature context-smoke \
      --output "$tmp_dir/second.json" \
      src/auth/service.ts src/users/repository.ts
    cmp "$tmp_dir/first.json" "$tmp_dir/second.json"

A successful run proves deterministic generation and replacement through the command's adapter invocation. Phase 6
adds the installed Spec Kit command-discovery smoke test.

## Constraints

- Never edit `.sdd` files.
- Never patch `.specify/`, `.specify-agent/`, or root `.specdd/` framework files to expose this command.
- Never duplicate persistent SpecDD constraints into feature artifacts.
- Never infer write authority from proximity, naming, or task grouping.
