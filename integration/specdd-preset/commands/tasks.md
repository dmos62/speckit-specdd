## SpecDD Task Augmentation

Apply these requirements while generating the upstream `tasks.md`. Preserve the upstream checklist format, execution ordering, and independent user-story structure.

1. Refresh the active Change Boundary with `speckit.specdd.context` before finalizing task write sets. Use exact implementation paths from the plan and proposed tasks; unresolved paths are not authority.
2. Preserve Spec Kit user-story grouping. A single user story may span multiple SpecDD authority domains.
3. Within each user-story phase, prefer implementation tasks whose non-`.sdd` write set has one primary SpecDD authority. When one proposed task spans authorities and the work is naturally separable, split it into authority-local tasks under the same user story rather than splitting the user story itself.
4. Keep legitimate cross-domain contract work together when decomposition would make the work less coherent and the current SpecDD authority model already permits every write. Do not treat `CROSS_BOUNDARY` as automatic invalidity.
5. Separate ordinary implementation from durable system evolution in task wording and sequencing:
   - normal implementation uses existing contracts and authority;
   - work classified as `SPEC_EVOLUTION_REQUIRED` names the `.sdd` contract that must change and remains distinct from implementation writes;
   - work classified as `AUTHORITY_EVOLUTION_REQUIRED` changes ownership or write permission in a standalone step, ends the current authority context, and requires a fresh `speckit.specdd.context` run before any later implementation task relies on the new authority.
6. Do not add custom bracket labels that would violate the upstream task checklist format. Keep task IDs, `[P]`, and `[US#]` semantics unchanged.
7. After generating `tasks.md`, invoke `speckit.specdd.validate` at the `tasks` stage. Correct stale or unresolved task scope before completion. Use `authorityGroups` to improve decomposition where useful, but never rewrite SpecDD authority to make a task valid.
8. Never synchronize Spec Kit task markers with SpecDD `Tasks:` entries and never parse `.sdd` source to infer ownership.
