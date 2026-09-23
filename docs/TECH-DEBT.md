# Technical Debt

This register contains unresolved risks in the currently implemented Spec Kit × SpecDD bridge while Boundary migrates to its native architecture.

Detailed implementation sequencing belongs in [TODO.md](TODO.md).

## Authorization scope is inferred from prose paths

Current task parsing discovers path-looking text from `tasks.md` and uses those paths in boundary and authorization logic.

An incidental reference can therefore become semantically significant even when it is not an intended write.

Preferred direction:

- make task write scope explicit;
- permit heuristic path discovery only for advisory planning;
- require authorization to consume structured exact writes.

## Dirty intended targets can be adopted by a new authorization

The current Git baseline excludes unchanged dirty state that existed at authorization.

If implementation occurs before authorization, or an implementation operation is reauthorized after producing changes, those changes can become indistinguishable from unrelated pre-authorization state.

Preferred direction:

- reject unverified dirty intended targets;
- close and verify an authorization epoch before scope expansion;
- allow dirty carry-forward only when exact state is proven by verified predecessor evidence.

## Authorization evidence is split across several writes

The current implementation writes boundary, specification/control selection, and Git-baseline documents separately.

A failure between writes can partially replace evidence even though failed authorization is intended to preserve the previous successful state.

Preferred direction:

- represent one operation with one atomic document;
- archive completed operation records independently when history is required.

## SpecDD semantics are duplicated in bridge code

Current code interprets `Owns`, `Can modify`, path expressions, and resolver-returned sections.

This makes the bridge responsible for part of SpecDD's authority semantics and creates edge cases such as not-yet-created directory ownership.

Preferred direction:

- implement Boundary's own deliberately smaller native contract semantics;
- isolate remaining SpecDD behavior in a temporary compatibility adapter;
- remove the adapter after native contract migration.

## Framework bootstrap pollutes agent context

`.specdd/bootstrap.md` is large, provider-specific, and contains material unrelated to normal Boundary implementation.

Loading it into agent context couples project procedure to a legacy framework and reduces cache efficiency.

Preferred direction:

- do not expose the SpecDD bootstrap to normal agents;
- use small stable Boundary skills;
- derive target-specific contract context on demand;
- remove `.specdd/` from downstream repositories.

## Public identity is coupled to implementation adapters

Current extension, commands, workflow state, source directories, and documentation expose Spec Kit and SpecDD as product concepts.

Preferred direction:

- make Boundary the product identity;
- treat Spec Kit as a change-system adapter;
- treat Codex as an agent-runtime adapter;
- treat SpecDD as migration compatibility only;
- remove obsolete public names rather than preserving compatibility aliases without a demonstrated downstream requirement.

## Temporary SpecDD provider uses a mutable branch identity

Development currently obtains the typed intended-target provider from a branch that reports package version `1.2.0`.

Different branch commits can therefore share the same version identity.

Preferred direction:

- pin the migration provider to an immutable revision while it remains necessary;
- remove the provider entirely once native contract resolution replaces it.
