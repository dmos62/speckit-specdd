---
schema: boundary.contract/v1
id: boundary-agent-procedure
owns:
  - skills/**
---

# Canonical Agent Procedure

## Purpose

Define stable Boundary procedure for scope planning, implementation, and contract evolution.

## Invariants

- Canonical skill files contain Boundary procedure only.
- Skills remain independent of current feature IDs, target paths, hashes, owners, generated operation state, and runtime-specific discovery paths.
- Skills describe lifecycle behavior while deterministic Boundary tooling remains authoritative.
- Project-specific contract facts are obtained through on-demand effective-context inspection.

## Prohibitions

- Canonical skills must not duplicate persistent project contracts.
- Canonical skills must not embed host-specific command syntax as required product semantics.

## Interfaces

- `boundary-scope`, `boundary-implement`, and `boundary-contracts` are the canonical procedural capabilities materialized by concrete runtimes.
