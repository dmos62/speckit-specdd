# Implementation TODO

Active work below is derived from `docs/TECH-DEBT.md`.

The v0.1 authority-hardening baseline is complete: immutable authorization evidence, effective-context freshness checks,
semantic Change Boundary consistency, explicit modification-permission projection, planned specification/control
verification, operation-scoped Git baselines, and generated Codex skill classification are implemented and covered by
the current test suite.

Project code and documentation have been refocused so oversized design material is split by stable responsibility,
shared CLI output behavior is centralized, and active technical debt no longer retains completed P0 work.

## P2 — Intended-path resolver support

- [ ] Replace the current unsupported-creation fallback when SpecDD exposes resolver-backed intended-path authority.
  - Blocked as of 2026-09-18: pinned SpecDD CLI `1.1.1` requires `resolve` targets to exist.
  - Rechecked against the official `specdd/cli` repository on 2026-09-18: `main` still reports package version `1.1.1`,
    its `resolve` documentation explicitly requires targets to exist, and its latest changelog entry is `1.1.1`.
  - No released or documented machine-readable CLI command, flag, or API currently authorizes a non-existent ordinary
    target.
  - The current SpecDD framework describes intended ordinary paths conceptually, but that framework contract is not a
    substitute for resolver-backed authority in this bridge.
  - No bridge implementation change is justified while this interface is absent: local ownership parsing, temporary
    probe files, or undocumented CLI internals would create authority semantics outside the supported SpecDD resolver.
  - Resume this work only through a deliberate compatibility change to a released SpecDD CLI/API version that exposes
    authoritative machine-readable resolution for intended ordinary paths.
  - When that interface exists, update the pinned compatibility contract deliberately before relying on it.
  - Cover exact ownership, existing-directory ownership, glob ownership, `Can modify`, ambiguous ownership, and no
    authority.
  - Preserve `.sdd` evolution-path exclusion from implementation boundaries.
  - Prove task-stage validation and pre-implementation authorization can carry resolver-backed intended targets without
    weakening the authority-snapshot invariant.
  - Remove the `INTENDED_TARGET_UNSUPPORTED` fallback only after those tests establish semantic parity with SpecDD
    intended-path rules.
