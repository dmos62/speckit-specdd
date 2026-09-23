# Active debugging: immutable distribution lifecycle regression

## Current failure

The full Python test suite has one failure:

- `preset_test_distribution.DistributionInstallTests.test_immutable_archive_runs_lifecycle_without_vendored_bridge_source`

The installed downstream runtime reaches verification, but verification reports `AUTHORITY_VIOLATION` for `src/app.py`.

Observed verification state:

- actual target: `src/app.py`
- actual authority: the downstream temporary `.sdd` authority
- planned target count: `0`
- planned authorities: empty
- authorization Git baseline otherwise exists and is readable
- generated installation files are correctly classified as preauthorization state
- SpecDD lint succeeds

This means the immediate problem is not inability to install or execute the immutable distribution. The authorization snapshot reaching verification contains no planned implementation target for `src/app.py`.

## Working hypothesis

Recent explicit-write authorization behavior likely made the immutable-distribution fixture stale.

The supported bridge semantics require implementation scope to come from dedicated `Writes:` metadata rather than incidental path-looking task prose. If this distribution test still constructs a task without explicit write metadata, authorization can legitimately produce an empty planned target set and verification will later reject the real write.

Do not weaken explicit-write authorization merely to make this fixture pass.

## Investigation order

1. Read `preset_test_distribution.py` and its setup helpers to find the exact generated task text used by the failing test.
2. Confirm whether the task that drives authorization declares `Writes: src/app.py` using the syntax accepted by the installed bridge.
3. If explicit write metadata is absent, update the fixture/setup and keep production authorization strict.
4. If metadata is already present, trace the installed archive command path through authorization and determine where the write declaration is lost.
5. Re-run the single failing distribution test.
6. Re-run `test_verification.py`.
7. Run bootstrap check.
8. Re-run the full `test_*.py` suite.

## Constraints

- Preserve the requirement that authorization scope comes only from explicit structured writes.
- Preserve the immutable-archive test's purpose: a downstream consumer without vendored canonical bridge source must complete the supported installed lifecycle.
- Do not hide the regression by excluding the distribution test from the full suite.
- Keep generated installation state classified outside implementation writes.
- Delete this file once the regression is resolved and the focused/full suites pass.
