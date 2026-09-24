---
schema: boundary.contract/v1
id: boundary-verification
owns:
  - src/boundary/verification/**
depends_on:
  - boundary-authorization
  - boundary-context
  - boundary-native-contracts
---

# Operation Verification

## Purpose

Derive actual Git writes and verify them against historical Boundary authorization.

## Invariants

- Actual writes are derived from Git final state relative to the authorization baseline.
- A changed Git `HEAD` invalidates direct verification against the recorded baseline.
- Every ordinary actual write must be present in the exact authorized target set.
- Actual implementation targets are fresh-resolved and compared with their historical effective-context identities.
- Successful verification records exact final dirty states for later verified carry-forward.

## Prohibitions

- Current task prose or regenerated planning state must not replace historical operation evidence.
- Adapter-owned path classification must not hide native contracts or explicitly authorized targets.
- Contract evolution must not be treated as retroactive implementation authority.

## Interfaces

- Verification services expose provider-neutral diagnostics and close successful authorization epochs.
