---
schema: boundary.contract/v1
id: boundary-repository-tooling
owns:
  - scripts/**
---

# Repository Tooling

## Purpose

Provide reproducible Boundary development bootstrap and downstream integration reconstruction.

## Invariants

- Downstream Boundary source identity is committed as one immutable lock containing an exact source revision and archive checksum.
- Locked remote source is checksum-verified before extraction or installation.
- Install, health-check, remove/reinstall, and deliberate upgrade operate from the committed Boundary lock.
- Generated Boundary integration state remains reconstructible from canonical source and is excluded locally rather than becoming downstream canonical source.
- Shared host registry and configuration files remain visible to Git rather than being hidden as Boundary-owned generated state.
- Installation and removal use supported host lifecycle mechanisms rather than patching generated state directly.
- Development bootstrap remains separate from downstream locked-source reconstruction.
- Development bootstrap does not install or require the removed SpecDD migration provider.
- Installation failures identify missing prerequisites before relying on partially initialized generated state.

## Prohibitions

- Generated integration state must not become canonical Boundary source.
- Mutable remote sources must not be treated as reproducible immutable installation inputs.
- Upgrade must not silently follow a branch, tag alias, or latest release.
- Legacy `.specdd/` state must not be created as part of Boundary installation.

## Interfaces

- `scripts/consumer.py` reconstructs downstream Boundary state from `boundary.lock.json`.
- `scripts/install.sh` installs already materialized Boundary source for development or the locked consumer.
