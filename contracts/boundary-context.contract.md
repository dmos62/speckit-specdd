---
schema: boundary.contract/v1
id: boundary-context
owns:
  - src/boundary/context/**
depends_on:
  - boundary-native-contracts
  - boundary-repository
---

# Effective Target Context

## Purpose

Project the canonical contract facts relevant to one repository target.

## Invariants

- Target context is disposable query output rather than persistent project state.
- Every matching ownership or applicability contract contributes additively.
- Direct dependencies expose relevant interface context without recursively importing unrelated internal constraints.
- Every projected semantic item retains canonical source provenance.

## Prohibitions

- Effective context must not become a feature-local authorization cache.
- Unrelated project contracts must not be automatically loaded into normal target context.

## Interfaces

- `resolve_target_context` returns ownership, applicable contracts, semantic projections, dependency interfaces, and provenance for one target.
