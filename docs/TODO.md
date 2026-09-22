# Implementation TODO

Active work below is derived from the current bridge limitation.

The v0.1 authority-hardening baseline is complete. Current bootstrap, SpecDD lint, and focused Change Boundary tests pass.

## P2 — Intended-path resolver support

- [ ] Integrate resolver-backed intended-path authority after upstream SpecDD CLI support is released.
  - A pre-release implementation is available at `https://github.com/dmos62/specdd-cli` on branch
    `feature/resolve-intended-targets`.
  - `HUMAN-REQUEST.md` defines the local usage and development setup needed to exercise that fork before publication.
  - The fork retains package version `1.1.1`; do not change the bridge compatibility pin solely to distinguish the fork.
    Verify the intended-target flags and behavior directly.
  - Current published SpecDD CLI as of 2026-09-21 is `1.1.1`.
  - The upstream implementation handoff is `HUMAN-REQUEST-UPSTREAM-SPECDD-CLI.md`. It remains the acceptance reference
    until the functionality is released upstream.
  - Required upstream interface: mutually exclusive `--file`, `--folder`, and `--sdd-file` flags that allow non-existent
    targets to be resolved without changing unflagged existing-target behavior.
  - Do not emulate intended-target resolution locally through `Owns`/`Can modify` parsing, temporary probe files, or
    undocumented CLI internals.
  - When the upstream feature is published, deliberately update the compatibility pin before depending on the released
    version.
  - Replace `INTENDED_TARGET_UNSUPPORTED` fallback handling with resolver-backed intended-target resolution while
    preserving current target normalization and Change Boundary semantic validation.
  - Cover exact ownership, directory ownership, glob ownership, `Can modify`, ambiguous ownership, absent authority,
    ordinary files, directories, and `.sdd` intended targets as applicable to bridge behavior.
  - Preserve `.sdd` evolution-path and root bootstrap-control exclusion from implementation boundaries.
  - Prove task-stage validation and pre-implementation authorization can carry resolver-backed intended targets without
    weakening the authority-snapshot invariant.
  - Remove `INTENDED_TARGET_UNSUPPORTED` behavior and documentation only after released-CLI tests establish semantic
    parity.
