---
schema: boundary.contract/v1
id: boundary-core
owns:
  - src/boundary/**
---

# Boundary Core

## Purpose

Provide provider-neutral Boundary mechanics and product concepts.

## Invariants

- Boundary product semantics remain independent of any particular change system, contract provider, or agent runtime.
- Facts that can be computed deterministically remain deterministic code responsibilities.
- Generated projections, adapter state, and operation evidence do not become persistent project contracts.

## Prohibitions

- Core semantics must not depend on Spec Kit command names, SpecDD concepts, or agent-runtime discovery paths.
- Agent prompt compliance must not become the authorization or correctness boundary.

## Interfaces

- Core packages expose repository paths, native contracts, target context, authorization, verification, and product CLI behavior through provider-neutral APIs.
