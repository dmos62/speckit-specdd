---
schema: boundary.contract/v1
id: boundary-native-contracts
owns:
  - src/boundary/contracts/**
depends_on:
  - boundary-repository
---

# Native Contract Engine

## Purpose

Discover, parse, validate, and construct the canonical Boundary contract graph.

## Invariants

- Canonical contracts are discovered only from `contracts/**/*.contract.md`.
- Contract file placement has no semantic effect beyond canonical discovery.
- Ownership and applicability use only exact paths and subtree scopes ending in `/**`.
- Applicability is additive and nested ownership selects one most-specific owner without removing broader constraints.
- Contract graphs are rebuilt deterministically from canonical contract contents.

## Prohibitions

- The native engine must not implement SpecDD bootstrap, `Can modify`, nearest-file inheritance, or arbitrary glob semantics.
- The native engine must not persist a second compiled copy of canonical contract prose.

## Interfaces

- `ContractGraph` is the transient validated graph representation.
- `load_contract_graph` loads fresh canonical contracts for consumers.
