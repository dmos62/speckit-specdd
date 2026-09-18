# Implementation TODO

Active work below is derived from `docs/TECH-DEBT.md`.

The v0.1 authority-hardening baseline is complete: immutable authorization evidence, effective-context freshness checks, semantic Change Boundary consistency, explicit modification-permission projection, planned specification/control verification, operation-scoped Git baselines, and generated Codex skill classification are implemented and covered by the current test suite.

Project code and documentation have been refocused so oversized design material is split by stable responsibility, shared CLI output behavior is centralized, and active technical debt no longer retains completed P0 work.

## P2 — Intended-path resolver support

- [ ] Replace the current unsupported-creation fallback when SpecDD exposes resolver-backed intended-path authority.
  - Current pinned CLI `1.1.1` accepts only existing resolver targets; do not emulate missing-path resolution by parsing `.sdd` ownership locally or by creating temporary probe files in the worktree.
  - When an authoritative CLI/API query becomes available, cover exact ownership, existing-directory ownership, glob ownership, `Can modify`, ambiguous ownership, and no authority.
  - Preserve `.sdd` evolution-path exclusion from implementation boundaries.
  - Remove the `INTENDED_TARGET_UNSUPPORTED` fallback only after task-stage and authorization tests prove semantic parity with SpecDD intended-path rules.
