---
schema: boundary.contract/v1
id: boundary-documentation
owns:
  - README.md
  - docs/**
---

# Boundary Documentation

## Purpose

Document the current Boundary architecture, development state, and migration without conflating transitional integrations with product concepts.

## Invariants

- Current architecture documentation distinguishes durable Boundary concepts from Spec Kit, SpecDD, and agent-runtime integrations.
- Migration work remains separated from target architecture statements.
- Documentation stays focused and delegates detailed semantics to the focused specification that owns them.
- Historical material is clearly distinguishable from current target behavior.
- Downstream consumer reconstruction is documented separately from Boundary source-development setup.

## Prohibitions

- Transitional provider behavior must not be presented as a permanent Boundary requirement.
- Documentation must not introduce a global project-contract or bootstrap model absent from the product specification.
