# Implementation TODO

The bridge currently targets the fork-backed SpecDD CLI `1.2.0` with typed intended-target resolution enabled. Repository
bootstrap builds and installs `https://github.com/dmos62/specdd-cli.git` from branch
`feature/resolve-intended-targets` when the active CLI does not satisfy the version and resolver-capability checks.

The compatibility fallback for older non-pinned resolvers remains intentionally conservative. The supported development
path is the pinned fork until an equivalent published upstream package is available.

## P1 — Fail when the pinned resolver lacks required intended-target capabilities

- [ ] Distinguish supported compatibility fallback from a broken pinned SpecDD CLI installation.
  - Continue producing conservative `INTENDED_TARGET_UNSUPPORTED` records for older, non-pinned resolvers that do not
    expose `--file`, `--folder`, and `--sdd-file`.
  - Treat SpecDD CLI `1.2.0` without the complete typed intended-target flag set as an infrastructure/toolchain failure
    instead of silently degrading to compatibility behavior.
  - Reuse the existing CLI version and `resolve --help` capability checks rather than introducing a second capability
    model.
  - Add focused tests for an older unsupported resolver, a malformed pinned resolver, and a correctly capable pinned
    resolver.
  - Keep bootstrap and bridge diagnostics aligned so the same invalid pinned installation is not accepted by one layer
    and rejected by another.

## P2 — Define ownership semantics beneath not-yet-created directories

- [ ] Resolve whether an exact owned path such as `Owns: ./future-domain` can authorize intended descendants before that
  directory exists.
  - Determine the intended SpecDD framework and resolver contract before changing bridge ownership matching.
  - Do not infer directory intent locally from `.sdd` text or filesystem absence; the bridge must continue to consume
    resolver semantics rather than implement a parallel SpecDD parser.
  - If resolver output can distinguish the ownership shape unambiguously, project that information through the existing
    ownership calculation.
  - If the contract remains ambiguous, keep the result conservative and document that an exact missing ownership path
    cannot act as directory ownership until its type is knowable.
  - Add focused coverage for existing owned directories, missing owned directories, exact intended files, glob-owned
    intended files, and intended-versus-created resolution parity.
