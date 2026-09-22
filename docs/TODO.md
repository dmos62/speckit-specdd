# Implementation TODO

The bridge currently targets the fork-backed SpecDD CLI `1.2.0` with typed intended-target resolution enabled. Repository
bootstrap builds and installs `https://github.com/dmos62/specdd-cli.git` from branch
`feature/resolve-intended-targets` when the active CLI does not satisfy the version and resolver-capability checks.

The compatibility fallback for older non-pinned resolvers remains intentionally conservative. A version-matching
SpecDD CLI `1.2.0` installation without the complete typed intended-target flag set is treated as a broken pinned
toolchain rather than compatibility behavior.

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
