## Boundary Write Scope

Apply these requirements while generating the upstream `tasks.md`. Preserve the upstream checklist format, execution ordering, and independent user-story structure.

1. Identify exact repository-relative implementation targets rather than inferring scope from descriptive prose.
2. Inspect candidate target context on demand with `boundary inspect <target...>` when ownership, invariants, prohibitions, or dependency interfaces are needed during task refinement.
3. For every implementation task, add one dedicated indented `Writes:` line directly below the checklist task. It must contain one or more exact repository-relative implementation paths in backticks. Separate multiple backticked path tokens with commas or whitespace, with no prose between tokens.
4. Treat only that `Writes:` metadata as structured implementation scope for the Spec Kit adapter. Path-looking prose elsewhere in the task remains advisory.
5. Do not declare the same write target in more than one task. Repeated structured ownership is ambiguous and Boundary authorization rejects it.
6. Preserve normal Spec Kit task IDs, ordering, `[P]`, and `[US#]` semantics.
7. Prefer owner-local tasks when work separates cleanly without harming the user-story implementation.
8. Keep legitimate coordinated multi-owner work together when that is the clearer implementation unit; every exact path still remains independently authorized by Boundary.
9. Keep native contract evolution separate from ordinary implementation. Use the `boundary-contracts` procedure for persistent contract changes and require fresh implementation authorization afterward.
10. Do not put native contract files in an ordinary implementation task's `Writes:` metadata.
11. When implementation scope changes after authorization, update structured task scope only after leaving the current implementation operation, then require fresh `speckit.boundary.authorize`.
12. Do not create or refresh a persisted Boundary context projection during planning or task generation.
13. Do not add a separate validation lifecycle phase. Deterministic structural enforcement occurs at authorization and verification.
