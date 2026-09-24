---
schema: boundary.contract/v1
id: boundary-authorization
owns:
  - src/boundary/authorization/**
depends_on:
  - boundary-context
  - boundary-native-contracts
  - boundary-repository
---

# Operation Authorization

## Purpose

Authorize exact operation write scope against fresh contracts and current Git state.

## Invariants

- Implementation scope comes only from explicit structured write declarations.
- Every implementation target resolves through a fresh native contract graph to one unambiguous owner.
- Implementation and contract evolution are separate operation kinds.
- Successful authorization creates one atomic operation record with the Git baseline and governing target identities.
- Dirty intended targets require exact verified predecessor provenance before carry-forward.
- An unverified active operation cannot be silently replaced.

## Prohibitions

- Path-looking prose must not widen implementation authority.
- Native contract changes must not authorize implementation writes in the same operation.
- Mutable planning state must not alter historical authorization evidence.

## Interfaces

- Authorization services produce and persist versioned `OperationRecord` evidence for implementation and contract-evolution operations.
