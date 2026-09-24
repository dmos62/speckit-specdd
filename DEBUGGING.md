# SpecDD framework-bootstrap regression

## Current failure

The distribution test `test_immutable_archive_runs_lifecycle_without_vendored_bridge_source` fails when the installed workflow gate runs its `context` stage.

Observed diagnostic:

    workflow_gate.py: Could not determine the SpecDD framework version from <consumer-root>

The focused preset suite and the full test suite both have this single failure. Canonical agent-skill tests pass.

## Expected behavior

The isolated downstream consumer intentionally has no `.specdd/bootstrap.md`.

This is required by the current Boundary architecture:

- Boundary bootstrap does not initialize or require the SpecDD framework bootstrap for normal operation.
- The temporary SpecDD compatibility CLI remains a resolver dependency during migration.
- Legacy `.sdd` contracts may still be resolved by the compatibility adapter without making SpecDD framework bootstrap state an agent-instruction or runtime prerequisite.
- `scripts/scripts.sdd` already states that bootstrap/check mode must not depend on SpecDD framework bootstrap state.

Do not fix this by creating `.specdd/bootstrap.md` in the consumer fixture or weakening the distribution test.

## Investigation target

Inspect `integration/specdd/scripts/workflow_gate.py` and its local imports for framework-version discovery.

Determine why the runtime still attempts to discover a SpecDD framework version before the `context` stage can execute. Remove that dependency where it is unrelated to resolver capability or canonical compatibility behavior.

Preserve capability-based checks for typed intended-target support. The compatibility behavior should depend on resolver capabilities such as `--file`, `--folder`, and `--sdd-file`, not on framework-bootstrap files.

Also inspect focused workflow-gate tests for assumptions that still require framework initialization and update them to cover operation without `.specdd/bootstrap.md`.

## Verification

Run in this order:

    PYTHONPATH=src uv run --no-project python -m unittest discover -s tests -p 'test_workflow.py'

    PYTHONPATH=src uv run --no-project python -m unittest discover -s tests -p 'test_preset.py'

    PYTHONPATH=src uv run --no-project python -m unittest discover -s tests -p 'test_*.py'

Delete this file once the regression is fixed and the focused/full suites pass.
