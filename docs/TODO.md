# Implementation TODO

Current bridge hardening is complete. Intended-path resolver transport is implemented on the temporary SpecDD CLI fork
and the development integration remains capability-detected. The fork at
`https://github.com/dmos62/specdd-cli`, branch `feature/resolve-intended-targets`, now reports package version `1.2.0`.

The repository compatibility pin intentionally remains on the published `specdd@1.1.1` until an upstream release
containing intended-target resolution is available. `HUMAN-REQUEST.md` documents how to link and develop against the
temporary `1.2.0` fork without treating that local package version as a published compatibility release.

## P2 — Released intended-path resolver finalization

- [ ] Finalize the intended-path integration against a published upstream SpecDD CLI release.
  - The pre-release implementation remains at `https://github.com/dmos62/specdd-cli` on branch
    `feature/resolve-intended-targets` and currently reports package version `1.2.0`.
  - `HUMAN-REQUEST-UPSTREAM-SPECDD-CLI.md` remains the upstream acceptance reference until publication.
  - After release, verify `npm view specdd version`, installed `specdd resolve --help`, and intended-target resolution
    using the published package rather than the fork.
  - Deliberately update the repository compatibility pin to the released version before making typed intended-target
    support mandatory.
  - Run the full boundary, validation, workflow, verification, preset, bootstrap, and SpecDD lint suites against the
    released package.
  - Remove `INTENDED_TARGET_UNSUPPORTED` capability fallback behavior only after published-package parity is proven.
  - Update user-facing resolver and Change Boundary documentation for the released behavior, then remove obsolete
    pre-release handoff material.
