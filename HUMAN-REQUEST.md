# Human Request: Activate the Codex Spec Kit Integration

Phase 11 changes the supported local Spec Kit integration from `generic` to the registrar-backed `codex` integration. The generated Spec Kit state must be migrated through the supported CLI so the new extension commands, preset augmentations, and lifecycle hooks can be exercised in the real repository.

The latest check-only run still reports the `generic` integration and no `.agents/skills` directory. That is expected before migration: `bash scripts/bootstrap.sh --check` verifies state but does not change it.

From the repository root in bash, run the apply-mode bootstrap:

    bash scripts/bootstrap.sh

Then run:

    uv run --no-project python -m unittest discover -s tests -p 'test_*.py'
    specdd lint tests/fixtures/specdd-two-domain
    git diff --check
    git status --short

Please provide the command output in the next programming iteration.

Do not manually edit `.specify/`, `.agents/skills/`, `.specify-agent/commands/`, or root `.specdd/` framework files to make the checks pass. Bootstrap uses `specify integration switch codex` and the supported extension/preset installation commands to regenerate that state.

After the migration and verification succeed, delete this file and remove the completed Phase 11 section from `docs/TODO.md`.
