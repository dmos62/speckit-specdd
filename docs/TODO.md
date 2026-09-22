# Implementation TODO

The bridge now targets the fork-backed SpecDD CLI `1.2.0` with typed intended-target resolution enabled. Repository
bootstrap builds and installs `https://github.com/dmos62/specdd-cli.git` from branch
`feature/resolve-intended-targets` when the active CLI does not satisfy the version and resolver-capability checks.

The compatibility fallback for older resolvers remains intentionally conservative for non-pinned environments. The
supported development path is the pinned fork until equivalent behavior is available from a published upstream package.

## P2 — Migrate from the fork to a published upstream release

- [ ] Replace the temporary fork source with a published upstream SpecDD CLI release once intended-target resolution is
  available there.
  - Verify `npm view specdd version`, installed `specdd resolve --help`, and intended-target resolution using the
    published package.
  - Deliberately change the repository CLI source and version pin together; do not silently substitute a published
    package that lacks `--file`, `--folder`, and `--sdd-file`.
  - Run the full boundary, validation, workflow, verification, preset, bootstrap, and SpecDD lint suites against the
    released package.
  - Remove `INTENDED_TARGET_UNSUPPORTED` compatibility fallback behavior only after published-package parity is proven
    and older external resolver compatibility is no longer useful.
  - Update user-facing resolver, development, and Change Boundary documentation for the published behavior.
  - Remove `HUMAN-REQUEST-UPSTREAM-SPECDD-CLI.md` after the published release satisfies its acceptance contract.
