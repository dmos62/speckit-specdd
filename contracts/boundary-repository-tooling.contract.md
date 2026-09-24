---
schema: boundary.contract/v1
id: boundary-repository-tooling
owns:
  - scripts/**
---

# Repository Tooling

## Purpose

Provide reproducible development bootstrap and integration installation tooling.

## Invariants

- Generated integration state remains reconstructible from canonical source.
- Installation and removal use supported host lifecycle mechanisms rather than patching generated state directly.
- Development bootstrap does not install or require the removed SpecDD migration provider.
- Installation failures identify missing prerequisites before relying on partially initialized generated state.

## Prohibitions

- Generated integration state must not become canonical Boundary source.
- Mutable remote sources must not be treated as reproducible immutable installation inputs.
- Legacy `.specdd/` state must not be created as part of Boundary installation.
