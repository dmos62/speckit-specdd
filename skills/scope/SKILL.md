# boundary-scope

Use this skill while planning implementation work or refining implementation tasks.

## Procedure

1. Start from the active change system's requested work and structured task state.
2. Separate ordinary implementation from persistent-contract evolution before declaring writes.
3. Identify the exact repository-relative targets the implementation intends to modify.
4. Inspect Boundary effective context for each candidate target.
5. Confirm that every implementation target has one unambiguous primary owner.
6. Read the applicable invariants, prohibitions, and relevant dependency interfaces returned for each target.
7. Treat all applicable contracts additively, including broader owning contracts that continue to constrain a more specifically owned target.
8. Record the exact implementation writes through the active change system's structured write declaration.
9. Prefer owner-local tasks when the work separates cleanly without harming coherence.
10. Keep coordinated multi-owner work together when that is the clearer implementation unit.
11. Re-inspect targets when planning changes enough that the intended write set or relevant relationships change.

## Guardrails

- Path-looking prose is advisory context, not implementation authority.
- Exploratory targets do not belong in the declared write set unless implementation is expected to modify them.
- Do not infer permission from an owner name, nearby file, similar task, or previous operation.
- Do not authorize implementation from this skill.
- Do not mix native contract edits with implementation writes.
- Do not create a persisted planning projection merely to cache effective context.

## Handoff

Implementation-ready scope has exact declared writes and enough inspected effective context to explain why those targets are coherent.

Authorization remains a separate deterministic transition performed against fresh canonical contracts and current repository state.
