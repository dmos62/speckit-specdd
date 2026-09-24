# Downstream Distribution and Reconstruction

Boundary downstream installation is reproducible from one committed immutable source lock without carrying canonical Boundary implementation source in the consumer repository.

## Canonical downstream state

Boundary-specific downstream canonical state is limited to:

- native project contracts under `contracts/`;
- change-system artifacts that describe active product work;
- `boundary.lock.json`.

Installed runtime copies, extensions, presets, workflow overlays, materialized agent skills, caches, install provenance, and operation evidence are not canonical project semantics.

## Boundary lock

`boundary.lock.json` uses schema `boundary.lock/v1`.

Its source record contains exactly:

- `url`: an HTTPS GitHub archive URL for one exact 40-character commit;
- `revision`: that exact Git commit identity;
- `sha256`: the SHA-256 identity of the downloaded archive bytes.

The revision encoded by the archive URL must equal the explicit revision field.

A branch archive, tag archive, release alias, latest-release URL, or other mutable source selector is not a valid downstream lock source.

The checksum is verified before source extraction or installation.

The lock describes Boundary source identity rather than generated integration state.

## Reconstruction

The downstream consumer performs reconstruction in this order:

1. read and validate the committed lock;
2. download the exact archive named by the lock;
3. verify its SHA-256 checksum;
4. extract and validate the expected Boundary source tree;
5. delegate installation to the installer from that locked source;
6. install or select the supported Spec Kit integration baseline;
7. install the Spec Kit extension, task preset, and workflow overlay;
8. materialize the native Boundary runtime and canonical Codex skills;
9. record generated source provenance matching the lock;
10. maintain local Git exclusions for Boundary-owned generated state.

The generated runtime therefore comes from the same archive whose identity is committed in the project.

A fresh downstream clone does not need `src/boundary/`, `skills/`, `adapters/`, or `integration/` as canonical project source.

## Generated-state exclusion

Boundary-owned generated integration state is kept out of normal downstream Git status through a managed block in the current worktree's Git `info/exclude`.

This avoids making project `.gitignore` part of Boundary's canonical installation semantics.

The managed exclusions cover:

- materialized Boundary skills;
- generated Spec Kit Boundary command skills;
- installed Boundary runtime source;
- the Boundary extension;
- the Boundary preset;
- the Boundary workflow overlay.

Change-system feature artifacts are not broadly ignored.

Shared host registries are not hidden merely because Boundary has an entry in them. Clean-consumer coverage must establish whether such files need a more precise supported treatment.

## Lifecycle commands

The downstream consumer supports five explicit lifecycle operations.

`install` reconstructs generated state from the committed lock.

`check` confirms installed source provenance, generated-state exclusions, and the health checks supplied by the locked Boundary source.

`remove` removes the installed Boundary integration and its managed local exclusions.

`reinstall` removes and reconstructs the same locked version.

`upgrade` requires a new explicit immutable source URL, revision, and checksum. It installs that source before replacing the committed lock. A failed upgrade attempts to restore the previous locked installation.

No lifecycle operation follows a mutable latest release implicitly.

## Development installation

Boundary source development uses `scripts/bootstrap.sh` or `scripts/install.sh --source <local-source>`.

The source installer accepts only already materialized local source directories or local archives.

Unchecked remote installation is deliberately separated from source-development setup. Downstream remote reconstruction belongs to the lock-aware consumer.

## Failure behavior

Reconstruction fails before installation when:

- the lock schema is malformed;
- the source selector is mutable;
- the revision and URL disagree;
- the archive checksum differs;
- the archive lacks required Boundary source;
- required local host tools cannot be established.

Health checking fails when installed provenance no longer equals the committed lock or when generated integration state is incomplete.

Upgrade failure does not silently advance the lock.
