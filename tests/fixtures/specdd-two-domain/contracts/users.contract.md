---
schema: boundary.contract/v1
id: users
owns:
  - src/users/identity-contract.ts
  - src/users/future-identity-contract.ts
  - src/users/repository.ts
---

# Users

## Purpose

Provide external identity lookup while keeping Users persistence internals locally owned.

## Invariants

- `ExternalIdentityLookup` exposes lookup without repository mutation capabilities.

## Interfaces

- Consumers use `ExternalIdentityLookup` for external identity lookup.
