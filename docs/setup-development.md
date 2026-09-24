# Boundary Development Setup

This guide is for contributors working on Boundary source itself.

Downstream project installation is documented separately in [setup-downstream.md](setup-downstream.md).

## Bootstrap the source repository

Run:

    bash scripts/bootstrap.sh

The bootstrap establishes the repository's supported Spec Kit and Codex integration baseline, then installs the current local Boundary source.

Check an existing development installation with:

    bash scripts/bootstrap.sh --check

## Reinstall local source directly

For development iterations, run:

    bash scripts/install.sh --source .

The source installer accepts an already materialized local Boundary directory or local archive.

It does not fetch unchecked remote Boundary source. Remote downstream reconstruction uses `boundary.lock.json` and `scripts/consumer.py`.

## Core checks

Validate native contracts:

    PYTHONPATH=src uv run --no-project python -m boundary contracts check

Run native Boundary tests:

    PYTHONPATH=src uv run --no-project \
      python -m unittest discover -s tests -p 'test_native_*.py'

Run Spec Kit adapter tests:

    PYTHONPATH=src:integration/speckit/scripts uv run --no-project \
      python -m unittest discover -s tests -p 'test_spec_kit_adapter*.py'

Run downstream lock tests:

    PYTHONPATH=src uv run --no-project \
      python -m unittest discover -s tests -p 'test_consumer*.py'

## Source and generated state

Canonical Boundary source includes `src/boundary/`, canonical skills, concrete adapters, integration source, scripts, contracts, and documentation.

Generated `.specify/` installation state and materialized `.agents/skills/` outputs are not replacements for that source.

The Boundary source repository therefore uses local-source development procedures rather than treating its own downstream consumer lock as its development bootstrap.
