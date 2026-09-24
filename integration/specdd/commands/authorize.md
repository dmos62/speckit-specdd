---
description: Authorize structured Spec Kit implementation scope with Boundary.
---

## User Input

User input: `$ARGUMENTS`

User input may clarify the active work but cannot widen structured write scope or weaken deterministic Boundary findings.

## Goal

Act only as the Spec Kit change-system adapter for implementation entry.

The wrapper reads the active feature's structured task state, projects exact implementation `Writes:` declarations into Boundary's provider-neutral change model, and invokes fresh native Boundary implementation authorization.

It does not maintain a separate context or validation lifecycle state.

## Execution

1. Resolve the active Spec Kit feature through supported project state.
2. Require the active feature's `tasks.md`.
3. Project checklist tasks in file order.
4. Preserve each task ID and user-story label when present.
5. Read implementation scope only from dedicated indented `Writes:` metadata.
6. Ignore incidental path-looking prose for authorization scope.
7. Invoke the installed Boundary adapter gate:

       uv run --no-project python .specify/extensions/specdd/scripts/adapter_gate.py authorize

8. Boundary then:
   - reloads canonical native contracts;
   - resolves every declared target's current owner and effective context;
   - rejects native contract paths from implementation operations;
   - captures the current Git authorization baseline;
   - verifies predecessor provenance for any already-dirty target;
   - atomically stores the successful operation record in current-worktree Git metadata.

## Failure behavior

Malformed task state, missing structured writes, unowned targets, ambiguous ownership, invalid canonical contracts, pre-authorization target modifications without verified provenance, and stale active operations are blocking.

Do not regenerate a planning projection or reinterpret descriptive task prose to make authorization succeed.

## Constraints

- This command is a Spec Kit adapter wrapper, not a second Boundary product CLI.
- Do not edit tasks.
- Do not infer write scope from prose.
- Do not mix native contract edits into implementation scope.
- Do not replace deterministic Boundary failures with agent judgment.
