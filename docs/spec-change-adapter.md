# Change-System Adapter Architecture

Boundary treats a change system as an adapter that supplies structured implementation intent and lifecycle integration.

The adapter contract is provider-neutral. Host-specific workflow names, feature file names, command names, constitution concepts, and generated directory layouts do not belong in Boundary core.

## Responsibilities

A change-system adapter supplies:

- the active change identity;
- stable task identities and task order;
- exact implementation writes declared by each task;
- adapter-owned feature or generated paths;
- implementation lifecycle entry and exit integration.

Boundary supplies:

- native contract discovery and effective context;
- implementation authorization;
- operation records and authorization epochs;
- Git baselines and actual-write derivation;
- contract-evolution separation;
- implementation verification.

An adapter translates host state. It does not decide whether an implementation write is authorized.

## Active change identity

The adapter exposes one opaque, non-empty change ID for the active change.

Boundary does not interpret the ID's syntax and does not derive product semantics from it.

The ID must remain stable for the logical change while implementation authorization and verification refer to that change.

A host may use a directory name, database identifier, branch-associated record, or another native identity internally. That representation remains adapter-specific.

## Task scope

The adapter projects implementation tasks as an ordered sequence.

Each task contains:

- one opaque, non-empty task ID;
- zero or more exact repository-relative implementation write paths.

Task IDs must be unique within the active change.

Task order is preserved because diagnostics and authorization evidence may refer back to the host's task order.

Boundary does not infer writes from descriptive prose, path-shaped text, headings, or owner names.

The adapter must use the host's structured write declaration mechanism.

## Explicit writes

Implementation writes are exact repository-relative paths.

The change-level write projection is the deterministic ordered union of task writes, preserving first occurrence.

Duplicate declarations that make structured scope ambiguous should be rejected rather than silently normalized into a different task model.

A declared write expresses implementation intent only. It does not itself grant permission.

Boundary authorization resolves the declared target against fresh canonical contracts and current repository state.

## Adapter-owned paths

The adapter may identify paths that belong to change-system bookkeeping rather than product implementation.

Examples include host-owned feature state or generated lifecycle artifacts.

Adapter-owned path rules must be deterministic and repository-relative. They may use exact paths or explicitly declared subtrees when the host owns an entire generated subtree.

Adapter-owned classification must not:

- hide a path that is in the active declared implementation write set;
- hide a native Boundary contract write;
- convert an otherwise unauthorized implementation write into generated state;
- depend on free-form task prose;
- depend on whether verification would otherwise fail.

Boundary may exclude valid adapter-owned state from implementation actual-write diagnostics while continuing to verify declared implementation targets normally.

The concrete path vocabulary remains in the adapter. Boundary core receives only the normalized classification.

## Implementation lifecycle

Boundary recognizes two structural integration points for ordinary implementation.

### Entry

At implementation entry, the adapter supplies a fresh normalized change projection.

Boundary authorization then evaluates:

- active change identity;
- task identities and order;
- exact declared writes;
- canonical target context;
- current Git state;
- predecessor evidence when applicable.

Implementation may begin only after Boundary records a successful authorization operation.

Planning-time inspection is not an authorization transition.

### Exit

At implementation exit, Boundary verifies the active operation from repository state.

Verification derives actual writes from Git and compares them with the authorized write set while accounting for valid adapter-owned state.

The adapter may allow its host workflow to continue only after the Boundary verification transition returns its result.

Ordinary tests and host workflow completion do not substitute for Boundary verification.

## Scope expansion

When implementation discovers an additional required write:

1. the active implementation operation does not gain permission implicitly;
2. the current operation must leave implementation through the supported Boundary lifecycle;
3. the adapter updates structured task scope in its own change system;
4. Boundary receives a fresh normalized change projection;
5. fresh implementation authorization is required.

Previous verified work may carry forward only through Boundary's deterministic predecessor evidence.

## Contract evolution

Persistent contract evolution is separate from implementation scope supplied by a change adapter.

A contract-evolution operation modifies only native Boundary contract files.

Changing host task scope does not authorize contract edits.

After contract evolution completes, dependent implementation requires a fresh adapter projection and fresh Boundary implementation authorization.

## On-demand context

Target inspection is a Boundary query, not a change-system lifecycle state.

Planning tools may invoke `boundary inspect <target...>` whenever target context is needed.

Adapters should not create a persisted context phase or copy canonical contract semantics into host feature artifacts merely to make them available to agents.

## Concrete Spec Kit adapter

The Spec Kit adapter uses the active feature directory name as its opaque change identity and preserves task order from `tasks.md`.

Implementation write scope comes only from dedicated indented `Writes:` metadata attached to checklist tasks. Backticked repository-relative paths in that metadata are projected as exact writes. Incidental path-looking prose elsewhere in a task is not authorization input.

The adapter is installed with Spec Kit extension identity `boundary`. Under Spec Kit's canonical extension-command namespace, this yields the two public wrappers:

- `speckit.boundary.authorize` at implementation entry;
- `speckit.boundary.verify` at implementation exit.

Those wrappers invoke native Boundary authorization and verification. They are adapter commands, not alternate product identities.

Spec Kit planning and task refinement use `boundary inspect` on demand. There is no public persisted context phase and no public validation phase.

The Spec Kit workflow overlay owns the two blocking lifecycle transitions. The extension does not duplicate them as hooks.

Spec Kit feature artifacts and `.specify/` state are adapter-owned for actual-write classification unless a path is itself an authorized implementation target or a native Boundary contract. That classification cannot hide an authorized or contract path because Boundary checks those classes before consulting the adapter classifier.

Legacy SpecDD bridge scripts may remain temporarily for migration and parity evidence. They are not part of the normalized Spec Kit change projection and do not grant implementation authority.

## Core isolation

Boundary core must not contain assumptions about:

- host feature directory names;
- host task document names or syntax;
- workflow stage names;
- host command namespaces;
- constitutions or equivalent host policy documents;
- extension, preset, hook, or overlay concepts;
- generated agent discovery paths.

Those concerns belong to concrete adapters.

A replacement change system should therefore require a new adapter implementation, not changes to native contracts, authorization, agent procedure, or verification semantics.

## Determinism

Given the same host change state, the adapter must produce the same normalized projection.

Adapter projection must not depend on transient agent conversation state.

Authorization and verification consume fresh adapter projections at their respective lifecycle transitions rather than trusting a stale planning projection.

## Failure behavior

Malformed or ambiguous structured change state is a blocking adapter error.

Missing change identity, duplicate task identity, invalid write paths, or an invalid adapter-owned path declaration must not be converted into permissive defaults.

When the adapter cannot represent required implementation scope, implementation remains unauthorized until the host state is corrected.
