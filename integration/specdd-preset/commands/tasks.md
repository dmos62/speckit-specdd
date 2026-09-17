## SpecDD Task Augmentation

Apply these requirements while generating the upstream `tasks.md`. Preserve the upstream checklist format, execution
ordering, and independent user-story structure.

1. Refresh the active Change Boundary with `speckit.specdd.context` before finalizing task write sets. Use exact
   implementation paths from the plan and proposed tasks; unresolved paths are not authority.
2. Preserve Spec Kit user-story grouping. A single user story may span multiple SpecDD authority domains.
3. Within each user-story phase, prefer implementation tasks whose non-`.sdd` write set has one primary SpecDD
   authority. When one proposed task spans authorities and the work is naturally separable, split it into authority-local
   tasks under the same user story rather than splitting the user story itself.
4. Keep legitimate cross-domain contract work together when decomposition would make the work less coherent and the
   current SpecDD authority model already permits every write. Do not treat `CROSS_BOUNDARY` as automatic invalidity.
5. Separate ordinary implementation from durable system evolution in task wording and sequencing:
   - normal implementation uses existing contracts and authority;
   - spec evolution uses the ordinary task-text prefix `SPEC_EVOLUTION_REQUIRED:` and names only the `.sdd` contract or
     contracts that must change;
   - authority evolution uses the ordinary task-text prefix `AUTHORITY_EVOLUTION_REQUIRED:` and names only the `.sdd`
     contract or contracts that change ownership or write permission;
   - never combine an evolution task's `.sdd` targets with non-`.sdd` implementation writes in the same task;
   - these prefixes are text inside a normal Spec Kit task description, not additional bracket labels or authority.
6. After a deliberate spec-evolution task, generate a separate follow-up task that refreshes `speckit.specdd.context`
   before the first implementation task that depends on the changed specification. An `AUTHORITY_EVOLUTION_REQUIRED:`
   task ends the prior authority context; newly proposed authority is unusable until that follow-up refresh produces a
   fresh Change Boundary.
7. Do not add custom bracket labels that would violate the upstream task checklist format. Keep task IDs, `[P]`, and
   `[US#]` semantics unchanged.
8. After generating `tasks.md`, invoke `speckit.specdd.validate` at the `tasks` stage. Correct stale, unresolved, mixed
   evolution/implementation, or malformed evolution scope before completion. Use `authorityGroups` to improve
   decomposition where useful, but never rewrite SpecDD authority to make a task valid.
9. Never synchronize Spec Kit task markers with SpecDD `Tasks:` entries and never parse `.sdd` source to infer ownership.
