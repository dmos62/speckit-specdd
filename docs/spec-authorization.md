# Authorization and Operation Evidence

Boundary turns explicit change-system write declarations plus fresh native contracts into historical evidence for one operation. Authorization does not depend on a persisted planning boundary.

## Explicit write declarations

Implementation scope is structured and exact. For the current Spec Kit adapter, the intended task shape is equivalent to:

    - [ ] T012 [US2] Implement authenticated callback handling
      Writes: `src/auth/callback.ts`, `src/auth/session.ts`

Path mentions elsewhere in task prose never widen authority. Planning may heuristically inspect path-looking prose because planning output cannot grant write permission.

## Operation kinds

Boundary v1 has two operation kinds.

### Implementation

An implementation operation:

- authorizes exact ordinary project paths;
- requires one unambiguous primary owner for every target;
- may span several owners;
- may not modify native contracts.

There is no task-level synthetic authority identity. Multi-owner work is one operation with targets owned by different contracts.

### Contract evolution

A contract-evolution operation:

- authorizes exact `contracts/**/*.contract.md` paths;
- may create, modify, or delete contracts;
- may not modify ordinary implementation files;
- must be followed by structural contract validation before dependent implementation.

Changed contracts never authorize implementation writes in the same operation.

## Authorization inputs and checks

Implementation authorization consumes:

- active change identity;
- task identities where available;
- exact declared write targets;
- a freshly loaded native `ContractGraph`;
- current Git `HEAD`;
- exact current index/worktree dirty state;
- adapter classification of generated and change-system-owned paths where needed by integration.

It verifies canonical paths, operation kind, unambiguous ownership, resolvable effective context, internally consistent task scope, verified predecessor closure, dirty-target provenance, and reliable Git capture.

No feature-local Change Boundary or refresh-time context sidecar is required.

## Dirty-target provenance

An intended path must not silently adopt unverified pre-authorization work.

Unrelated dirty paths are allowed and recorded in the baseline. A dirty intended target is accepted only when:

- the current predecessor is verified;
- it belongs to the same change and operation kind;
- it recorded a verified final state for that exact target;
- the target's current Git state exactly equals that recorded state.

Git state identity includes index and worktree state, so staging, unstaging, deletion, mode changes, symlinks, and content changes affect identity.

Otherwise authorization fails with `DIRTY_TARGET_NOT_VERIFIED`.

This prevents both pre-authorize modification adoption and mutation of verified predecessor output before a successor epoch.

## Atomic operation record

Each successful authorization creates one versioned operation document containing, conceptually:

    schemaVersion
    operationId
    changeId
    kind
    tasks
    authorizedTargets
      path
      owner
      effectiveContextIdentity
    contractGraphIdentity
    gitBaseline
      head
      dirtyPathStates
    carriedForward
      path
      state
      operationId
    verification
      finalPathStates
    status

One operation is never split across independently writable boundary, selection, and baseline documents.

`status: verified` closes the authorization epoch and permits replacement.

## Storage and atomicity

Operation evidence lives in current-worktree Git metadata, for example:

    <git-dir>/boundary/current.json
    <git-dir>/boundary/operations/<operation-id>.json

`current.json` is the active epoch. A verified predecessor is archived immutably only when a successor depends on its carry-forward evidence.

Creating or replacing active evidence is transactional from the caller's perspective. Construction or write failure must leave the previous successful record usable. Temporary files followed by atomic replacement are preferred.

When carry-forward is required, the verified predecessor is archived before successor installation. A later successor-write failure leaves the prior current record usable; the immutable archive is harmless.

Operation evidence is workflow history, not a persistent project contract.

## Contract and Git identities

Authorization records enough identity to prove what governed each target without duplicating contract prose.

`effectiveContextIdentity` derives from canonical contracts contributing to a target's effective context. Verification fresh-resolves actual targets and compares current effective identity with historical target evidence.

The Git baseline records authorization-time `HEAD` plus exact index/worktree identities for dirty paths present at authorization.

A baseline dirty path whose state is unchanged is not an operation write. A baseline dirty path that changes, or a clean path that becomes dirty, enters operation scope.

A changed `HEAD` invalidates direct comparison. Verification fails closed with `GIT_BASELINE_CHANGED` rather than attributing changes across commits or resets.

## Verification

Verification derives post-authorization writes from Git final state and the historical operation record.

For implementation it:

- excludes unchanged baseline dirty state;
- separates adapter-owned generated/change-system state when the adapter classifies it as such;
- rejects native contract changes;
- rejects every ordinary write absent from the exact authorized target set, even when its owner is already represented;
- fresh-resolves actual ordinary targets through the native graph;
- rejects unowned or ambiguous targets;
- detects changed effective contract context.

Adapter classification cannot hide native contract paths or paths already present in the operation's authorized target set.

For contract evolution, verification checks exact contract-write authority and rejects ordinary project writes. Structural contract validation remains a separate `boundary contracts check` concern.

Current tasks, planning projections, feature convergence, tests, and semantic review do not participate in authorization verification.

## Verification closure

Successful verification records the exact final dirty-state identity of every authorized target that remains dirty. Those states are the only states eligible for later carry-forward.

Closure also confirms that Git `HEAD` still equals the authorization baseline before marking the operation verified.

## Scope expansion

When implementation discovers another required target:

1. stop before writing it;
2. verify and close the current operation;
3. preserve verified final states of completed targets;
4. authorize a fresh write set;
5. carry forward only exact verified predecessor states;
6. archive the predecessor only when the successor relies on that evidence;
7. continue implementation.

This preserves completed work without widening stale authority.

## Provider-neutral diagnostics

Native authorization and verification prefer product-level codes such as:

- `INVALID_WRITE_TARGET`;
- `UNOWNED_WRITE_TARGET`;
- `AMBIGUOUS_OWNERSHIP`;
- `UNDECLARED_WRITE`;
- `CONTRACT_CONTEXT_CHANGED`;
- `OPERATION_KIND_VIOLATION`;
- `DIRTY_TARGET_NOT_VERIFIED`;
- `GIT_BASELINE_CHANGED`;
- `CONTRACT_GRAPH_INVALID`.

Legacy provider diagnostics stay inside migration adapters.
