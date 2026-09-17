# Human request: initialize and inspect the integration lab

The repository bootstrap changes external tool installations and creates upstream-generated Spec Kit and SpecDD state, so run it from the actual development checkout rather than simulating those files manually.

From the repository root:

    node --version
    npm --version
    uv --version
    bash scripts/bootstrap.sh
    git status --short
    bash scripts/bootstrap.sh --check

Inspect the generated `.specify/`, `.specify-agent/`, and `.specdd/` files for anything unexpected. If the output is clean and the checks pass, commit the initialized baseline:

    git add .
    git commit -m "Bootstrap Spec Kit and SpecDD integration lab"

Return the complete output of `bash scripts/bootstrap.sh --check` and `git status --short` after the commit. Once that output has been reviewed, delete this file and the remaining Phase 0 items from `docs/TODO.md`.
