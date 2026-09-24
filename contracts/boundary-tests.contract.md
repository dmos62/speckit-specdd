---
schema: boundary.contract/v1
id: boundary-tests
owns:
  - tests/**
---

# Boundary Tests

## Purpose

Protect native Boundary behavior and concrete supported integrations with focused tests.

## Invariants

- Tests exercise public behavior and deterministic boundaries without duplicating production implementations.
- Native tests keep provider-neutral core behavior independent of Spec Kit and historical providers.
- Concrete adapter tests verify projection and lifecycle behavior without redefining core authorization semantics.
- Repository contract coverage verifies representative ownership and additive applicability of canonical native contracts.
- Historical migration assertions do not define current Boundary semantics.

## Prohibitions

- Legacy compatibility behavior must not be promoted into native semantics solely because an old test asserts it.
- Tests must not require a generalized provider framework absent from the product architecture.
