---
schema: boundary.contract/v1
id: auth
owns:
  - src/auth/service.ts
  - src/auth/future-service.ts
depends_on:
  - users
---

# Auth

## Purpose

Authenticate external identities through the Users-facing identity lookup interface.

## Invariants

- External identity lookup uses `ExternalIdentityLookup`.

## Prohibitions

- Auth code must not depend on Users persistence internals.
