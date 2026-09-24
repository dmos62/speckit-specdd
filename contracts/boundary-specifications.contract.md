---
schema: boundary.contract/v1
id: boundary-specifications
owns:
  - docs/spec.md
  - docs/spec-architecture.md
  - docs/spec-contracts.md
  - docs/spec-agent-instructions.md
  - docs/spec-authorization.md
  - docs/spec-change-adapter.md
  - docs/spec-lifecycle.md
  - docs/spec-distribution.md
  - docs/spec-v0.1.md
---

# Boundary Specifications

## Purpose

Define Boundary's product model through focused, orthogonal architecture specifications.

## Invariants

- Focused specifications divide product concerns by responsibility rather than by current provider.
- Native contracts, target context, authorization, verification, change-system integration, agent instruction delivery, and downstream reconstruction retain explicit responsibility boundaries.
- Target architecture takes precedence over historical migration behavior.
- Historical v0.1 material remains descriptive evidence rather than a current product contract.

## Prohibitions

- Focused specifications must not duplicate detailed migration checklists from `docs/TODO.md`.
- Historical SpecDD compatibility semantics must not silently become native Boundary requirements.
