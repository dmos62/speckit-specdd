---
schema: boundary.contract/v1
id: boundary-agent-adapters
owns:
  - adapters/**
depends_on:
  - boundary-agent-procedure
---

# Agent Runtime Adapters

## Purpose

Materialize canonical Boundary procedure into concrete supported agent runtimes.

## Invariants

- Runtime adapters add only fixed discovery metadata around canonical skill procedure.
- Materialization is deterministic and idempotent.
- Generated skill bytes are independent of feature, task, authorization, and operation state.
- Codex and Claude Code remain concrete adapters rather than members of a generalized provider framework.

## Prohibitions

- Concrete runtime differences must not leak into canonical Boundary skill content.
- Runtime adapters must not become a second source of canonical procedure.

## Interfaces

- Concrete materializers reproduce the named Boundary skills in each runtime's supported discovery location.
