---
schema: boundary.contract/v1
id: boundary-change-adapter-migration
owns:
  - integration/**
---

# Change Adapter Migration Source

## Purpose

Contain the current Spec Kit integration and temporary SpecDD compatibility implementation while migration to native Boundary semantics is completed.

## Invariants

- Change-system integration remains an adapter around native Boundary authorization and verification semantics.
- SpecDD resolver, bootstrap, permission, and `.sdd` behavior is migration compatibility only.
- Explicit structured task writes are the implementation-scope input that survives migration.
- Host-generated state remains separate from canonical Boundary source.

## Prohibitions

- Compatibility code must not define Boundary core APIs or native contract semantics.
- Legacy Change Boundary state must not become required native planning or authorization state.
- SpecDD provider identity must not become a Boundary runtime or product identity.
