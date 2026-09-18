# v0.1 Scope and Acceptance

This document records the initial release contract for the Spec Kit × SpecDD bridge.

## Required scope

v0.1 includes:

1. a local integration-lab repository;
2. initialized Spec Kit and SpecDD state;
3. a local Spec Kit extension;
4. `speckit.specdd.context`;
5. `speckit.specdd.validate`;
6. `speckit.specdd.authorize`;
7. `speckit.specdd.verify`;
8. machine-readable SpecDD resolution through the existing CLI;
9. Change Boundary schema version `1`;
10. derived feature `boundary.json`;
11. planning preset augmentation;
12. task-generation preset augmentation;
13. convergence preset augmentation;
14. structural workflow gates;
15. authority-domain task validation;
16. explicit separation of implementation, specification evolution, and authority evolution;
17. a multi-domain fixture;
18. tests for expected valid and invalid cases;
19. documentation sufficient to install and exercise the integration locally.

The initial release does not require:

- automatic `.sdd` editing;
- automatic authority changes;
- Spec Kit and SpecDD task synchronization;
- remote registry publishing;
- a general-purpose persistent bridge database;
- complex dependency-graph optimization;
- upstream forks.

## Integration fixture

The deterministic fixture contains independent Auth and Users domains.

Auth owns its authentication service. Users owns its identity contract and repository. Auth may modify the Users-facing identity contract through explicit non-owning authority, while Users retains ownership. Auth has no permission to modify Users repository internals.

This fixture establishes both cross-domain collaboration and the distinction between ownership and modification permission.

## Required scenarios

### Valid local change

A task modifies only Auth-owned implementation under applicable Auth constraints.

Expected outcome:

- the boundary resolves;
- task validation succeeds;
- authorization can succeed;
- verification accepts the resulting local write.

### Accidental authority violation

Auth-oriented work directly modifies Users repository internals without permission.

Expected outcome:

- the bridge identifies the cross-owned write;
- implementation authority is rejected;
- correction targets task structure or implementation path rather than weakening SpecDD.

### Valid cross-domain feature

One feature requires coordinated Auth and Users changes.

Expected outcome:

- the feature remains one Spec Kit feature;
- authority-local tasks are preferred where practical;
- legitimate coordinated work remains representable;
- both owner domains appear in the Change Boundary.

### Valid non-owning modification

One task deliberately uses Auth authority to modify the Users-facing identity contract.

Expected outcome:

- Users remains the target owner;
- Auth is shown separately as an allowed modifying authority;
- the applicable `Can modify` source remains visible.

### Deliberate system-contract evolution

A feature genuinely requires a new persistent Auth-to-Users contract.

Expected outcome:

- the bridge identifies specification evolution;
- the durable `.sdd` target is explicit;
- ordinary implementation does not proceed under nonexistent authority;
- dependent implementation receives fresh context and authorization afterward.

### Authority evolution

A feature genuinely changes which domain may modify a target.

Expected outcome:

- the bridge identifies authority evolution;
- the current operation receives no immediate new rights;
- the prior authority context ends;
- dependent implementation begins only after specification evolution, fresh context, and new authorization.

### Governing-context drift

A governing `Must`, `Forbids`, reference, referenced contract, governing chain, or resolver generation identity changes after boundary refresh.

Expected outcome:

- authorization reports blocking `STALE_BOUNDARY`;
- the stale boundary is not made current inside authorization;
- context must be refreshed deliberately.

### Operation-baseline isolation

The worktree contains dirty state before authorization.

Expected outcome:

- authorization records exact dirty-path identities;
- unchanged pre-authorization state is excluded from verification;
- any later content or deletion change participates in verification;
- changed Git `HEAD` requires fresh authorization.

## Acceptance criteria

v0.1 is acceptable when:

- Spec Kit and SpecDD coexist in the same repository;
- the bridge installs without modifying Spec Kit core;
- the bridge calls the real SpecDD resolver;
- a feature can generate deterministic derived Change Boundary state;
- governing-context drift is detected before authorization;
- malformed or semantically inconsistent boundaries are rejected;
- multi-domain features remain representable;
- ownership remains distinct from non-owning modification permission;
- unauthorized cross-domain writes are blocked;
- valid `Can modify` writes remain possible without ownership transfer;
- specification and authority evolution are explicit;
- evolution cannot retroactively authorize the same implementation operation;
- successful authorization preserves immutable historical evidence;
- verification compares post-baseline Git state with that historical evidence;
- changed `.sdd` and bootstrap-control state cannot silently authorize implementation;
- Spec Kit remains the canonical feature-task system;
- SpecDD remains the canonical persistent system-specification system;
- no copied persistent SpecDD rule set is maintained in Spec Kit feature files;
- no Spec Kit or SpecDD fork is required.

## Design principles

### Thin bridge

Translate only what is required for the two systems to cooperate.

### Derived state over duplicated state

Prefer recomputation and stable fingerprints to synchronized copies of persistent rules.

### One authority per concept

Do not create competing stores for feature intent, system contracts, governance, or task execution.

### Explicit system evolution

Architectural change is valid but must be deliberate and operationally separate from implementation that depends on the new contract.

### Feature cohesion plus authority locality

Keep a coherent Spec Kit feature while partitioning implementation by SpecDD authority where practical.

### Deterministic mechanics, agentic judgment

Automate objective path, resolver, authority, and evidence calculations. Use architectural reasoning only where mechanics cannot determine intent.

### Upstream replaceability

Depend on supported Spec Kit and SpecDD interfaces rather than patches.

### Progressive strictness

Allow exploratory uncertainty early and require exact authority before implementation.

## Future directions

Post-v0.1 work may include:

- richer semantic system-contract verification;
- specification-only workflow operations;
- structured task metadata when upstream Spec Kit exposes it;
- resolver-backed intended-path authority;
- broader host portability coverage;
- distributed authorization-evidence transport for CI;
- end-to-end workflow execution tests;
- richer traceability and visualization;
- explicit review mechanisms for architectural warnings.

Future work should preserve the central responsibility split rather than growing the bridge into a third source of truth.
