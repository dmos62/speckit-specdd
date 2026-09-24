# Downstream Boundary Setup

This guide is for repositories that consume Boundary without carrying Boundary implementation source.

Boundary source development is documented separately in [setup-development.md](setup-development.md).

## Prerequisites

The downstream machine needs:

- Git;
- `uv`;
- Codex.

The locked installer establishes the supported Spec Kit version when installation requires it.

## Canonical project state

Commit:

- native contracts under `contracts/`;
- the change-system artifacts your project uses;
- `boundary.lock.json`.

Do not commit generated Boundary runtime copies, installed adapter state, or materialized Boundary skills as Boundary source.

A lock has this shape:

    {
      "schema": "boundary.lock/v1",
      "source": {
        "revision": "<40-character Boundary commit>",
        "sha256": "<SHA-256 of the exact archive bytes>",
        "url": "https://github.com/<owner>/<repo>/archive/<commit>.tar.gz"
      }
    }

The commit in `url` and `revision` must be identical.

## Fresh clone reconstruction

After cloning the downstream repository, run the Boundary consumer utility from an available Boundary distribution or tooling checkout:

    python /path/to/boundary/scripts/consumer.py \
      --root /path/to/project \
      install

The consumer reads `/path/to/project/boundary.lock.json`, verifies the locked archive, and delegates installation to that exact Boundary source.

The downstream repository does not need a canonical `src/boundary/`, `skills/`, `adapters/`, or `integration/` tree.

## Health check

Run:

    python /path/to/boundary/scripts/consumer.py \
      --root /path/to/project \
      check

The check requires installed source provenance to match the committed lock and then runs the health check supplied by the locked source.

## Remove and reconstruct

Remove generated Boundary integration:

    python /path/to/boundary/scripts/consumer.py \
      --root /path/to/project \
      remove

Reconstruct the same locked version:

    python /path/to/boundary/scripts/consumer.py \
      --root /path/to/project \
      reinstall

## Deliberate upgrade

Determine the new exact Boundary commit and the SHA-256 of its exact GitHub commit archive.

Then run:

    python /path/to/boundary/scripts/consumer.py \
      --root /path/to/project \
      upgrade \
      --source https://github.com/<owner>/<repo>/archive/<commit>.tar.gz \
      --revision <commit> \
      --sha256 <archive-sha256>

The upgrade installs the candidate source before replacing `boundary.lock.json`.

Review and commit the resulting lock change deliberately. Boundary never follows a mutable release automatically.

## Generated state

Boundary maintains local Git exclusions in the worktree's Git metadata for Boundary-owned generated integration state.

Operation authorization evidence also lives in Git metadata rather than ordinary project source.

Shared Spec Kit registry or configuration files are not automatically ignored by Boundary. If installation changes shared host state, that change remains visible in Git status and should be handled according to the project's Spec Kit configuration policy.

Boundary-owned generated files can be removed and reconstructed without changing native project contracts.
