---
schema: boundary.contract/v1
id: boundary-cli
owns:
  - src/boundary/cli/**
  - src/boundary/__main__.py
depends_on:
  - boundary-context
  - boundary-native-contracts
---

# Boundary CLI

## Purpose

Expose product-level Boundary commands without coupling the core CLI to a host workflow.

## Invariants

- CLI commands use Boundary terminology and provider-neutral core APIs.
- Target inspection is transient and does not persist effective-context projections.
- Contract checking validates fresh canonical native contracts.

## Prohibitions

- Product CLI behavior must not depend on Spec Kit stages, SpecDD commands, or agent-runtime discovery paths.

## Interfaces

- The product command surface includes native contract checking and target inspection and may grow to expose native authorization and verification.
