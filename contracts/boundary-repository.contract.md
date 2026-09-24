---
schema: boundary.contract/v1
id: boundary-repository
owns:
  - src/boundary/repository/**
---

# Repository Paths

## Purpose

Provide canonical repository-relative path primitives shared by Boundary core.

## Invariants

- Canonical repository paths are non-empty relative POSIX paths.
- Path normalization does not depend on filesystem existence.
- Parent traversal, absolute paths, backslashes, and NUL bytes are rejected.

## Interfaces

- `normalize_repo_path` is the shared canonicalization boundary for repository targets.
