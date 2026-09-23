# Authorization and Operation Evidence

Boundary authorization turns explicit change-system write declarations plus fresh persistent contracts into historical evidence for one operation.

Authorization does not depend on a previously persisted planning boundary.

## Explicit write declarations

Implementation scope must be explicit.

For the current Spec Kit adapter, the intended task representation is structurally equivalent to:

    - [ ] T012 [US2] Implement authenticated callback handling
      Writes: `src/auth/callback.ts`, `src/auth/session.ts`

The exact adapter syntax may evolve, but authorization receives a structured ordered set of write targets.

Path mentions elsewhere in task prose do not widen that set.

Planning tools may heuristically extract paths for advisory inspection only.

## Operation kinds

Boundary v1 defines two operation kinds:

- `implementation`;
- `contract-evolution`.

### Implementation

An implementation operation:

- authorizes exact ordinary project write targets;
- requires every target to have one unambiguous owner;
- may span several owner domains;
- may not modify native contract files.

There is no task-level `SPECDD_AUTHORITY:` replacement in Boundary v1.

Multi-owner work is represented directly as one operation containing targets with different owners.

### Contract evolution

A contract-evolution operation:

- declares exact `contracts/**/*.contract.md` targets;
- may create, modify, or delete contracts;
- may not modify ordinary implementation files;
- must leave the resulting native contract graph structurally valid.

Contract changes never authorize dependent implementation in the same operation.

## Authorization inputs

Implementation authorization consumes:

- active change identifier from the change-system adapter;
- task identities where available;
- exact declared write targets;
- fresh native `ContractGraph`;
- current Git `HEAD`;
- current dirty worktree and index state;
- adapter classification of generated/change-system-owned paths.

No feature-local Change Boundary or refresh-time context sidecar is required.

## Authorization checks

Before an implementation operation is accepted, Boundary verifies:

- every write target is a valid canonical repository path;
- no write target is a native contract file;
- every write target has one unambiguous primary owner;
- effective target context can be derived;
- explicit task scope is internally consistent;
- an existing active authorization epoch has been verified before replacement;
- intended operation targets are not being silently adopted from unverified dirty state;
- Git state can be captured reliably.

Contract evolution performs the corresponding contract-target and Git checks without granting implementation authority.

## Dirty-state rule

A path intended for the new operation must not already contain unverified work that the operation would silently adopt.

Unrelated dirty paths may exist and are recorded in the Git baseline.

For v1, a dirty intended target is accepted only when:

- the current predecessor operation is verified;
- the predecessor belongs to the same change and operation kind;
- the predecessor recorded a verified final state for that exact target;
- the target's current Git state exactly equals that recorded final state.

The Git state identity includes both index and worktree state. Staging, unstaging, deletion, executable-mode changes, symlinks, and content changes therefore alter the identity even when ordinary file bytes alone would not expose the transition.

Otherwise authorization fails.

This prevents:

    modify target
    authorize
    verify

from treating the pre-authorization modification as out-of-scope baseline state.

It also prevents a verified predecessor output from being changed after verification and then silently adopted by a later authorization epoch.

## Operation record

Each successful authorization creates one atomic operation document.

Conceptually it records:

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

The exact schema should remain minimal and versioned.

One operation must not be split across separately writable boundary, selection, and baseline documents.

`status: verified` means that authorization epoch is closed and may be superseded.

## Storage

Operation evidence lives in current-worktree Git metadata, not in project source.

A target layout is:

    <git-dir>/boundary/current.json
    <git-dir>/boundary/operations/<operation-id>.json

`current.json` represents the current authorization epoch.

A verified predecessor is archived as an immutable operation document only when a successor depends on its carry-forward evidence.

A verified predecessor that is superseded without carry-forward need not be archived.

The storage design must preserve a prior successful operation if creation of a replacement authorization fails.

No operation evidence is a persistent project contract.

## Atomicity

Creating or replacing active operation state must be transactional from the caller's perspective.

A failure while constructing or writing new evidence must leave the previous successful evidence usable.

Temporary files followed by atomic replacement are preferred.

When carry-forward is required, the verified predecessor is archived before the successor current record is installed. If successor installation fails afterward, the prior current record remains usable and the immutable archive is harmless.

## Effective-context identity

Authorization records enough contract identity to prove what governed each target when the operation began.

The identity is derived from canonical native contracts contributing to that target's effective context.

Rule prose is not duplicated into the operation record unless required for a future audit format.

Verification uses current canonical contracts plus historical identities to detect contract-context changes relevant to the authorized operation.

## Git baseline

The operation baseline records:

- authorization-time `HEAD`;
- exact index/worktree identities for dirty paths that existed before the operation.

A path whose state remains exactly equal to the baseline is not an operation write.

A baseline dirty path that changes afterward enters operation scope.

A clean path that becomes dirty enters operation scope.

A changed Git `HEAD` invalidates direct baseline comparison. Verification fails closed rather than heuristically attributing changes across commits or resets.

## Verification closure

Successful verification records the final dirty-state identity of every authorized target that remains dirty.

Those final states are the only states eligible for later carry-forward.

Verification also confirms that Git `HEAD` still equals the authorization baseline before the operation can be marked verified.

The native verification implementation adds actual-write authorization checks separately; recording final states and closing an epoch does not weaken those checks.

## Verification

Verification derives actual post-authorization changes from Git.

For an implementation operation it:

- excludes unchanged baseline dirty state;
- separates change-system artifacts and generated adapter state;
- rejects native contract changes;
- requires every ordinary implementation write to appear in the exact authorized target set;
- fresh-resolves ownership and effective-context identity;
- detects contract-context changes;
- verifies carried-forward states where applicable.

Current tasks or planning projections cannot widen verification scope.

## Scope expansion

Discovering another necessary target is allowed.

Writing it under stale authorization is not.

Boundary v1 uses authorization epochs:

1. stop before writing the new target;
2. verify and close the current implementation operation;
3. preserve the verified final states of completed targets;
4. create a fresh authorization containing the required next write set;
5. carry forward prior dirty states only when they exactly match verified predecessor evidence;
6. archive that predecessor only when its evidence is required by the successor;
7. continue implementation.

This avoids silently absorbing already-produced implementation into a new pre-authorization baseline.

A future design may support richer nested authorization, but v1 does not require an event-sourced transaction system.

## Verification versus convergence

Authorization verification answers:

> Were the actual writes permitted by the historical operation?

It does not answer:

> Is the implementation semantically correct?

Contract structural validation, tests, feature convergence, and agentic review remain separate concerns.

The workflow may run them together, but the core APIs and diagnostics remain distinct.

## Provider-neutral diagnostics

The native implementation should prefer product-level diagnostics such as:

- `INVALID_WRITE_TARGET`;
- `UNOWNED_WRITE_TARGET`;
- `AMBIGUOUS_OWNERSHIP`;
- `UNDECLARED_WRITE`;
- `CONTRACT_CONTEXT_CHANGED`;
- `OPERATION_KIND_VIOLATION`;
- `DIRTY_TARGET_NOT_VERIFIED`;
- `GIT_BASELINE_CHANGED`;
- `CONTRACT_GRAPH_INVALID`.

Legacy SpecDD-specific diagnostics remain inside the migration adapter until that adapter is removed.
