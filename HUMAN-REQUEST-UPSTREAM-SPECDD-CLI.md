# Upstream SpecDD CLI Handoff: Resolve Intended Paths

## Goal

Fork the upstream `specdd` CLI and extend `specdd resolve` so it can resolve a target that does not exist yet when the caller explicitly declares what kind of target is intended.

Add three mutually exclusive optional flags:

    --file
    --folder
    --sdd-file

These flags provide the information that filesystem inspection cannot provide for a non-existent target.

This work belongs in the upstream SpecDD CLI. Downstream integrations should not emulate SpecDD resolution by parsing `.sdd` files themselves, creating temporary probe files, or depending on undocumented CLI internals.

## Current released behavior

As of 2026-09-21, the published npm package is:

    specdd@1.1.1

Current command help is:

    Usage: specdd resolve [options] <target>

    Resolve relevant SpecDD specs for a target path.

    Arguments:
      target              Directory, .sdd file, or ordinary file to resolve.

    Options:
      --root <path>       Root directory for resolution. Defaults to the current
                          directory.
      --section <name>    Section to include, or all. May be repeated. (default: [])
      --sections <names>  Comma-separated sections to include, or all.
      --depth <depth>     Soft-link expansion depth: non-negative integer or all.
                          (default: "2")
      --format <format>   Output format: text, json, or json-extended. (default:
                          "text")
      -h, --help          display help for command

`specdd resolve` currently requires its target to exist.

That prevents callers from resolving the effective SpecDD context for implementation files or directories that are planned but have not yet been created.

## Required CLI behavior

Add these options to `specdd resolve`:

    --file       Treat the target as an intended ordinary file.
    --folder     Treat the target as an intended directory.
    --sdd-file   Treat the target as an intended .sdd specification file.

The three flags must be mutually exclusive.

Without one of these flags, preserve the current behavior exactly: the target must exist and its kind is determined from the filesystem.

With one of these flags, a non-existent target is valid input and must be resolved according to the declared target kind.

The command must not create the target or any of its missing parent directories.

## Existing targets

The new flags are primarily intended for non-existent paths, but their behavior for existing paths should be deterministic.

When the target already exists and no kind flag is supplied, preserve existing behavior.

When the target already exists and a kind flag is supplied, validate that the declared kind agrees with the existing target.

Examples:

- `--file` requires an existing ordinary non-`.sdd` file.
- `--folder` requires an existing directory.
- `--sdd-file` requires an existing `.sdd` file.
- A mismatch fails with a clear non-zero error rather than silently changing target semantics.

Using `--file` for a `.sdd` path should be rejected. `.sdd` targets have distinct resolution semantics and should use `--sdd-file`.

## Intended-target semantics

The new behavior should reuse the existing SpecDD path-resolution engine. The change should be limited to supplying an explicit target classification when filesystem inspection cannot determine it.

A useful conceptual model is:

    target path
    target kind: file | folder | sdd-file
    target exists: true | false

Existing-target resolution may continue to infer the target kind when no flag is present.

Intended-target resolution receives the kind from the selected flag.

The resulting governing-spec resolution should otherwise use normal SpecDD semantics.

## Intended ordinary file

For a missing target supplied with `--file`:

1. Normalize the intended path using the same repository/content-root safety rules as an existing target.
2. Treat the target as an ordinary file.
3. Resolve vertical directory context from the selected content root toward the intended parent directory using the existing directories that can participate in resolution.
4. Apply the normal same-directory same-basename rule when the corresponding `.sdd` file already exists beside the intended file.
5. Include explicit `References` and other resolver-expanded context exactly as the normal resolver does.
6. Do not require an `Owns` or `Can modify` entry merely to return resolver context.
7. Do not create the file.

Example:

    specdd resolve --root /repo --file /repo/src/auth/new-service.ts --sections all --format json

If `/repo/src/auth/new-service.sdd` already exists and normally matches `new-service.ts`, it must participate exactly as it would after `new-service.ts` is created.

## Intended directory

For a missing target supplied with `--folder`:

1. Normalize the intended path under the selected content root.
2. Treat the target as a directory for resolution purposes.
3. Resolve the applicable existing ancestor context using the normal directory-resolution semantics.
4. Do not invent local files or directories that are absent.
5. Do not create the directory.

Example:

    specdd resolve --root /repo --folder /repo/src/new-domain --sections all --format json

The implementation should follow current SpecDD framework rules for which directory-level specs are applicable. The kind hint removes target-type ambiguity; it must not invent governing specs that normal SpecDD rules would not select.

## Intended `.sdd` file

For a missing target supplied with `--sdd-file`:

1. Require a `.sdd` target path.
2. Normalize the intended path under the selected content root.
3. Treat it as a specification target selected for creation.
4. Resolve bootstrap and applicable existing ancestry context without requiring the target specification itself to exist.
5. Do not require `Owns` or `Can modify` authorization for the missing `.sdd` file.
6. Do not synthesize the missing spec into resolver output.
7. Do not create the file.

Example:

    specdd resolve --root /repo --sdd-file /repo/src/auth/new-service.sdd --sections all --format json

This is context discovery for a future specification, not implementation authorization.

## Missing parent directories

The resolver should support intended paths whose immediate parent does not yet exist when the path can still be normalized safely beneath the selected content root.

Resolution should use the existing ancestor directories that actually exist and must not create temporary directories to make the current resolver accept the path.

For example:

    /repo/src/new-domain/internal/service.ts

may be supplied with `--file` even when `new-domain/` and `internal/` do not exist.

The resolver should use the applicable existing context from `/repo`, `/repo/src`, and any other existing ancestors allowed by normal SpecDD semantics.

## Output compatibility

Preserve the existing output formats and their semantic structure:

    text
    json
    json-extended

Downstream consumers already depend on resolver-returned governing specifications and section data. Intended targets should therefore use the same result shape as existing targets wherever possible.

Do not require downstream consumers to parse a second resolver format solely for intended paths.

Existing options must continue to work with intended targets:

    --root
    --section
    --sections
    --depth
    --format

In particular, this command must work for machine consumers:

    specdd resolve --root <root> --file <missing-target> --sections all --format json

A successfully resolved intended target must exit with status `0`.

## Error handling

Return a clear non-zero error for at least these cases:

- more than one target-kind flag is supplied;
- the target escapes the selected root;
- host-incompatible or otherwise invalid absolute path syntax is supplied;
- an existing target conflicts with the declared kind;
- `--sdd-file` is used for a path that is not a `.sdd` path;
- `--file` is used for an existing `.sdd` specification;
- normal resolver invariants fail.

Do not convert a missing path with a valid explicit kind into a generic "target does not exist" error.

## Backward compatibility

This feature must be additive.

Commands that do not use `--file`, `--folder`, or `--sdd-file` must retain current behavior, including the current requirement that an untyped target exist.

That makes the new functionality opt-in and avoids changing interpretation of existing scripts.

## Suggested implementation shape

Avoid scattering existence special cases through the resolver.

Prefer introducing or extending an internal target descriptor/classification step so downstream resolver logic receives a normalized target path and an explicit target kind regardless of whether the kind came from filesystem inspection or a command-line hint.

Conceptually:

    resolve target argument
        |
        +-- kind flag present
        |     validate explicit kind
        |     allow missing path
        |
        +-- no kind flag
              require existing path
              infer kind from filesystem
        |
        v
    common normalized SpecDD resolution

The normal resolver should remain authoritative for ancestry, basename matching, references, section filtering, depth expansion, and output formatting.

Do not implement a parallel "intended path resolver" that can drift from ordinary resolution semantics.

## Required tests

Add focused automated coverage for at least the following cases.

### Compatibility

- existing ordinary file without a kind flag resolves exactly as before;
- existing directory without a kind flag resolves exactly as before;
- existing `.sdd` target without a kind flag resolves exactly as before;
- a missing target without a kind flag still fails.

### Intended files

- missing ordinary file plus `--file` succeeds;
- same-directory same-basename `.sdd` context is included when applicable;
- root and ancestor governing context is preserved;
- explicit-reference expansion still works;
- section filtering and depth options still work.

### Intended directories

- missing directory plus `--folder` succeeds;
- applicable existing ancestor context is returned;
- nested missing directories do not require temporary filesystem creation.

### Intended specs

- missing `.sdd` target plus `--sdd-file` succeeds;
- the missing specification is not synthesized into the result;
- ancestor/bootstrap context is returned;
- no `Owns`/`Can modify` requirement is introduced for spec creation.

### Validation

- the three kind flags are mutually exclusive;
- existing file with `--folder` fails;
- existing folder with `--file` fails;
- existing ordinary file with `--sdd-file` fails;
- existing `.sdd` file with `--file` fails;
- non-`.sdd` path with `--sdd-file` fails;
- paths outside the selected root remain rejected.

### Formats

Exercise intended-target resolution using at least `text`, `json`, and `json-extended`, with machine-readable JSON tests validating the same governing context represented by ordinary resolution.

## Regression expectation

Where an intended target is created after an initial intended-path resolution, resolving that now-existing target without a kind flag should produce equivalent governing SpecDD context, assuming no governing files or configuration changed between the two calls.

This parity property is the main semantic guarantee needed by downstream tooling.

## Non-goals

Do not solve downstream ownership projection in the CLI as part of this change.

Do not add bridge-specific concepts such as feature boundaries, task authority, authorization snapshots, or operation evidence.

Do not parse `Owns` or `Can modify` differently just for intended targets.

Do not create temporary probe files or directories.

Do not make missing untyped targets succeed automatically.

Do not change the SpecDD specification language merely to support this transport feature unless an actual framework ambiguity is discovered during implementation.

## Documentation

Update the upstream `specdd resolve --help` output and CLI documentation to explain:

- the three new flags;
- their mutual exclusivity;
- that they allow resolution before target creation;
- that ordinary behavior is unchanged when no flag is provided;
- that the flags normally are unnecessary for existing targets.

If the project maintains release notes or a changelog, identify this as resolver support for explicitly typed intended targets.

## Release requirement

The downstream consumer cannot depend on this work until it is available through a released `specdd` package.

After implementation and tests are complete:

1. release a new SpecDD CLI version;
2. verify `npm view specdd version` reports that release;
3. verify installed `specdd resolve --help` exposes `--file`, `--folder`, and `--sdd-file`;
4. verify intended-path JSON resolution works using the published package rather than only a local checkout.

## Acceptance criteria

The upstream work is complete when all of these statements hold:

- `specdd resolve` can resolve a non-existent ordinary file with `--file`;
- it can resolve a non-existent directory with `--folder`;
- it can resolve a non-existent `.sdd` target with `--sdd-file`;
- the kind flags are mutually exclusive;
- existing unflagged behavior remains compatible;
- intended and subsequently created targets resolve to equivalent governing context when the surrounding SpecDD state is unchanged;
- no filesystem probe artifacts are created;
- existing section, depth, root, and output-format options continue to work;
- machine-readable output remains suitable for existing resolver consumers;
- the feature is covered by upstream automated tests;
- the functionality is available in a published npm release.
