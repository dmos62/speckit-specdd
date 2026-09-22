# Implementation TODO

Current bridge hardening is complete. The intended-path resolver transport is now implemented on the pre-release SpecDD
CLI fork and the development host has been verified with Node.js 22, Yarn 1.22.22, the forked `specdd@1.1.1`, all three
typed resolve flags, the missing-target smoke tests, and `bash scripts/bootstrap.sh --check`.

The bridge now capability-detects typed intended-target support. When the installed resolver exposes `--file`,
`--folder`, and `--sdd-file`, missing targets are resolved through the SpecDD CLI. The public `1.1.1` behavior remains
conservative: missing targets retain `INTENDED_TARGET_UNSUPPORTED` rather than being locally inferred.

## P2 — Released intended-path resolver finalization

- [ ] Finalize the intended-path integration against a published upstream SpecDD CLI release.
  - The pre-release implementation remains at `https://github.com/dmos62/specdd-cli` on branch
    `feature/resolve-intended-targets` and intentionally reports package version `1.1.1`.
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
