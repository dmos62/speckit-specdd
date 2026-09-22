# Technical Debt

## Fork-backed SpecDD CLI dependency

The bridge currently pins SpecDD CLI `1.2.0` but obtains that version from
`https://github.com/dmos62/specdd-cli.git` branch `feature/resolve-intended-targets`. The fork provides the typed
intended-target resolution required by the bridge, while relying on an unreleased branch leaves repository bootstrap
dependent on a temporary source rather than a published upstream package.

Preferred direction:

- Migrate the repository CLI source and version pin together to the first published upstream SpecDD CLI release that
  provides equivalent `--file`, `--folder`, and `--sdd-file` behavior.
- Prove published-package parity through package-version inspection, resolver help inspection, intended-target JSON
  resolution, and the full boundary, validation, workflow, verification, preset, bootstrap, and SpecDD lint suites.
- Update resolver, development, and Change Boundary documentation when the published package becomes the supported
  development path.
- Remove `HUMAN-REQUEST-UPSTREAM-SPECDD-CLI.md` after the published release satisfies its acceptance contract.
- Remove legacy `INTENDED_TARGET_UNSUPPORTED` compatibility behavior only if published-package parity is established and
  compatibility with older external resolvers is deliberately no longer required.
