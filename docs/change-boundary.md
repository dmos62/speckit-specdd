# Legacy Change Boundary Model

Status: current implementation reference; superseded as target architecture by [spec-authorization.md](spec-authorization.md)

The checked-in SpecDD-backed implementation currently uses a feature-scoped Change Boundary and separate refresh-time context evidence.

This document remains only to explain the executable migration baseline. New Boundary architecture must not depend on these artifacts.

## Current feature state

The existing bridge materializes:

    specs/<feature>/.specdd/boundary.json

The file projects current ordinary implementation targets onto SpecDD ownership.

It contains:

- resolved implementation targets;
- primary SpecDD authority;
- governing specs;
- distinct authority domains;
- unresolved diagnostics;
- SpecDD generation metadata.

It does not contain persistent SpecDD rule text.

## Current freshness evidence

Boundary refresh also writes per-target effective SpecDD context identities under current-worktree Git metadata.

Authorization fresh-resolves targets and rejects the candidate boundary when relevant SpecDD context differs.

This mechanism exists because authorization currently depends on a previously generated planning/task projection.

The target Boundary architecture removes this synchronization problem by deriving authorization directly from explicit writes plus a fresh native contract graph.

## Current authorization evidence

Successful authorization currently records three documents:

    <git-dir>/specdd/authorization-boundary.json
    <git-dir>/specdd/authorization-spec-evolution.json
    <git-dir>/specdd/authorization-git-baseline.json

They preserve:

- the exact validated Change Boundary;
- selected `.sdd` and bootstrap-control evolution;
- authorization-time Git `HEAD`;
- authorization-time dirty-path identities.

Verification uses these historical documents rather than mutable feature state.

The target architecture replaces the three related documents with one atomic operation record per authorization epoch.

## Current Git-baseline behavior

The existing baseline excludes dirty state that already existed at authorization when its content/deletion identity is unchanged at verification.

If a pre-existing dirty path changes afterward, it re-enters operation scope.

A clean path that becomes dirty is in operation scope.

A changed `HEAD` fails closed.

These mechanics are useful and should be preserved where compatible with the native operation model.

The target architecture additionally prevents an intended operation target from being silently adopted as pre-authorization dirty state unless its exact state is carried forward from verified predecessor evidence.

## Current ownership and modification permission

The existing bridge derives ownership from SpecDD `Owns`.

A task may declare `SPECDD_AUTHORITY:` so a separate SpecDD `Can modify` projection can permit cross-owned writes.

Boundary v1 does not preserve this synthetic operation-authority model.

Native implementation operations may contain targets from several owners directly. A future delegated-write concept should be added only if a concrete Boundary use case requires it.

## Current bootstrap controls

The existing implementation has special behavior for:

    .specdd/bootstrap.md
    .specdd/bootstrap.project.md
    .specdd/bootstrap.local.md

This is legacy provider state.

The target downstream architecture contains no `.specdd/` directory and no Boundary equivalent of the SpecDD framework bootstrap.

## Current lifecycle

The executable bridge currently uses:

    context → validate → authorize → implement → verify

and the installed Spec Kit workflow inserts corresponding structural gates.

The target lifecycle is:

    authorize → implement → verify

Planning and task generation use on-demand inspection and skills rather than persisted lifecycle state.

## Current intended-target behavior

The existing bridge needs typed SpecDD resolver flags for missing intended paths and otherwise emits `INTENDED_TARGET_UNSUPPORTED`.

Native Boundary path semantics remove this issue.

An exact native scope is exact whether or not the path exists.

A native subtree scope ending in `/**` denotes that subtree whether or not its directory exists.

## Migration rule

Until the native contract and authorization implementation replaces this code, current commands and tests must continue to describe actual behavior accurately.

Do not partially reinterpret current SpecDD evidence as native Boundary evidence.

Migration should introduce the native model behind focused tests, switch lifecycle consumers deliberately, and then delete this legacy state model.
