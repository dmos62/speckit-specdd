## SpecDD Task Augmentation

Apply these requirements while generating the upstream `tasks.md`. Preserve the upstream checklist format, execution
ordering, and independent user-story structure.

1. Refresh the active Change Boundary with `speckit.specdd.context` before finalizing ordinary implementation write
   sets. Use exact implementation paths from the plan and proposed tasks; unresolved paths are not authority.
2. Preserve Spec Kit user-story grouping. A single user story may span multiple SpecDD authority domains.
3. Within each user-story phase, prefer implementation tasks whose ordinary non-`.sdd` write set has one primary SpecDD
   authority. When one proposed task spans owners and the work is naturally separable, split it into owner-local tasks
   under the same user story rather than splitting the user story itself.
4. Keep legitimate coordinated cross-domain work together when decomposition would make the work less coherent. An
   unmarked multi-owner task executes under its participating owner domains and remains a `MULTI_AUTHORITY_TASK` warning.
5. When one task intentionally executes all ordinary implementation writes under a single SpecDD authority, add
   `SPECDD_AUTHORITY:` followed by that repository-relative `.sdd` path in backticks. Validation must prove that the
   declared authority owns or has inherited `Can modify` permission for every write target.
6. Separate ordinary implementation from durable system evolution:
   - normal implementation uses existing contracts and authority;
   - spec evolution uses `SPEC_EVOLUTION_REQUIRED:` and names only `.sdd` contracts;
   - authority evolution uses `AUTHORITY_EVOLUTION_REQUIRED:` and names only `.sdd` contracts that change ownership or
     write permission;
   - never combine evolution `.sdd` targets with ordinary implementation or root bootstrap-control writes in one task.
7. Treat root `.specdd/` bootstrap controls separately from implementation authority:
   - `.specdd/bootstrap.md` is immutable and must never be generated as a write task;
   - `.specdd/bootstrap.project.md` may be named only when the workflow deliberately selects that project override;
   - `.specdd/bootstrap.local.md` may be named only for deliberate local-operator state and remains generated/local;
   - other root `.specdd/` control paths must not be generated as ordinary implementation work.
8. After deliberate spec evolution, generate a separate context refresh before dependent implementation. Dependent
   implementation must then pass `speckit.specdd.authorize` so a new immutable authorization snapshot exists.
9. `AUTHORITY_EVOLUTION_REQUIRED:` ends the prior authority context. Proposed authority is unusable until evolution
   completes, context refreshes, and authorization succeeds again.
10. Do not add custom bracket labels. Keep upstream task IDs, `[P]`, and `[US#]` semantics unchanged.
11. After generating `tasks.md`, invoke `speckit.specdd.validate` at the `tasks` stage. Correct stale, unresolved,
    unpermitted declared-authority, mixed evolution/implementation, or malformed evolution scope before completion.
    Bootstrap-control authority is enforced by the authorization gate and later verified against immutable evidence.
12. Never synchronize Spec Kit task markers with SpecDD `Tasks:` entries and never parse `.sdd` source to infer
    ownership or modification permission.
