---
schema: boundary.contract/v1
id: boundary-tests
owns:
  - tests/**
---

# Boundary Tests

## Purpose

Protect native Boundary behavior, concrete integrations, and temporary migration compatibility with focused tests.

## Invariants

- Tests exercise public behavior and deterministic boundaries without duplicating production implementations.
- Native tests keep provider-neutral core behavior independent of Spec Kit and SpecDD.
- Migration parity covers only legacy semantics that native Boundary deliberately preserves.
- Provider-specific compatibility tests remain removable when their migration dependency disappears.
- Repository contract coverage verifies representative ownership and additive applicability of canonical native contracts.

## Prohibitions

- Legacy compatibility behavior must not be promoted into native semantics solely because an old test asserts it.
- Tests must not require a generalized provider framework absent from the product architecture.
