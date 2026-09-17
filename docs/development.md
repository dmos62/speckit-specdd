# Development Setup

This repository is an integration lab for Spec Kit and SpecDD. Keep upstream-generated state separate from bridge source and keep the toolchain pinned while v0.1 semantics are being proven.

## Compatibility baseline

Selected on 2026-09-17:

| Component | Pin | Reason |
| --- | --- | --- |
| Node.js | 22.x or newer | SpecDD CLI requires Node.js 22+; `.nvmrc` selects the minimum supported major. |
| uv | installed on the development host | Required for the supported Spec Kit installation path. |
| Spec Kit | 1.0.7 | Current stable release selected for v0.1 development. |
| SpecDD CLI | 1.1.1 | Current stable CLI release selected for v0.1 development. |
| SpecDD framework | 1.5 | Current framework release selected for authority semantics and bootstrap behavior. |

Upstream references used for this baseline:

- Spec Kit releases: https://github.com/github/spec-kit/releases
- Spec Kit installation: https://github.com/github/spec-kit/blob/main/docs/installation.md
- SpecDD CLI: https://github.com/specdd/cli
- SpecDD framework releases: https://github.com/specdd/specdd/releases

Do not silently advance these pins during v0.1. Upgrade them only as a deliberate compatibility task with the fixture and acceptance tests rerun.

## Prerequisites

Install Git, Node.js 22+, npm, and uv before running the repository bootstrap.

With nvm, the repository-selected Node major can be activated with:

    nvm install
    nvm use

Install uv using the official instructions for the development host if `uv --version` is unavailable.

## Bootstrap

From the repository root, run:

    bash scripts/bootstrap.sh

The script performs only repository bootstrap responsibilities:

- verifies Git, Node.js, npm, and uv,
- installs Spec Kit 1.0.7 with `uv tool`,
- installs SpecDD CLI 1.1.1 with npm,
- initializes Spec Kit in the current repository using the generic integration,
- writes generic Spec Kit command files under `.specify-agent/commands`,
- initializes SpecDD framework 1.5,
- runs the Spec Kit environment check,
- runs `specdd lint`.

The script intentionally refuses to rewrite an existing SpecDD bootstrap whose framework version differs from 1.5. Review such a version change explicitly instead of allowing bootstrap automation to mutate system semantics unexpectedly.

## Verify without changing the repository

Use the check mode for subsequent iterations:

    bash scripts/bootstrap.sh --check

The check verifies the pinned tool versions, initialized state, Spec Kit environment, and SpecDD lint result. `dev-scripts.include` runs this mode so the next programming iteration receives bootstrap failures directly.

## Baseline commit

After the first successful bootstrap:

    git status --short
    bash scripts/bootstrap.sh --check

Review the generated `.specify/`, `.specify-agent/`, and `.specdd/` state. Commit the clean initialized baseline before adding bridge code. Do not manually patch generated Spec Kit core files.

Spec Kit manages machine-local state under its own `.specify/.gitignore`. This repository additionally ignores `.specdd/bootstrap.local.md` and generated feature-level Change Boundary files.
