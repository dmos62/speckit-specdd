# Implementation TODO

Active work below is derived from the current bridge limitation.

The v0.1 authority-hardening baseline is complete. Current bootstrap, SpecDD lint, and focused Change Boundary tests pass.

## P2 — Intended-path resolver support

- [ ] Integrate resolver-backed intended-path authority after upstream SpecDD CLI support is released.
  - Current published SpecDD CLI as of 2026-09-21 is `1.1.1`.
  - `specdd resolve --help` still exposes no intended-target kind option and the current resolver requires targets to exist.
  - The upstream implementation handoff is `HUMAN-REQUEST-UPSTREAM-SPECDD-CLI.md`. It is deliberately self-contained so it can be copied to an upstream fixer who has no access to this repository.
  - Required upstream interface: mutually exclusive `--file`, `--folder`, and `--sdd-file` flags that allow non-existent targets to be resolved without changing unflagged existing-target behavior.
  - Do not emulate intended-target resolution locally through `Owns`/`Can modify` parsing, temporary probe files, or undocumented CLI internals.
  - When the upstream feature is published, deliberately update the compatibility pin before depending on it.
  - Replace `INTENDED_TARGET_UNSUPPORTED` fallback handling with resolver-backed intended-target resolution while preserving current target normalization and Change Boundary semantic validation.
  - Cover exact ownership, directory ownership, glob ownership, `Can modify`, ambiguous ownership, absent authority, ordinary files, directories, and `.sdd` intended targets as applicable to bridge behavior.
  - Preserve `.sdd` evolution-path and root bootstrap-control exclusion from implementation boundaries.
  - Prove task-stage validation and pre-implementation authorization can carry resolver-backed intended targets without weakening the authority-snapshot invariant.
  - Remove `INTENDED_TARGET_UNSUPPORTED` behavior and documentation only after released-CLI tests establish semantic parity.
