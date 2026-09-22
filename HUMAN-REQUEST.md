# Human Request: Activate the Intended-Target SpecDD CLI Fork

The intended-target resolver implementation is available in a temporary SpecDD CLI fork and needs to be the locally
active `specdd` executable so this repository can exercise `--file`, `--folder`, and `--sdd-file`.

Fork:

- Repository: https://github.com/dmos62/specdd-cli
- Branch: `feature/resolve-intended-targets`
- Current fork package version: `1.2.0`
- Usage reference:
  https://github.com/dmos62/specdd-cli/blob/feature/resolve-intended-targets/README.md
- Development reference:
  https://github.com/dmos62/specdd-cli/blob/feature/resolve-intended-targets/DEVELOPMENT.md

This repository still deliberately pins the published SpecDD CLI to `1.1.1`. Do not change that compatibility pin merely
to make the development fork pass bootstrap version checks. The pin should change only when the intended-target behavior
is available from a published upstream package and the release-finalization TODO is performed.

While the `1.2.0` fork is linked, `bash scripts/bootstrap.sh --check` is therefore expected to reject the CLI version
until the repository deliberately moves its compatibility pin.

## 1. Confirm host prerequisites

The CLI requires Node.js 22 or newer. The fork uses Yarn `1.22.22`.

The bridge development host also needs npm, Git, `uv`, and the Codex CLI.

Run:

    node --version
    npm --version
    git --version
    uv --version
    codex --version

Install the expected Yarn version if necessary:

    npm install --global yarn@1.22.22
    yarn --version

Expected Yarn version:

    1.22.22

## 2. Clone the fork outside this repository

Keep the CLI checkout beside this repository rather than inside it.

For example:

    cd ..
    git clone --branch feature/resolve-intended-targets https://github.com/dmos62/specdd-cli.git specdd-cli-intended-targets
    cd specdd-cli-intended-targets
    git status
    git branch --show-current

The active branch must be:

    feature/resolve-intended-targets

If the checkout already exists:

    cd ../specdd-cli-intended-targets
    git fetch origin
    git switch feature/resolve-intended-targets
    git pull --ff-only

## 3. Install, verify, and build the fork

From the fork checkout:

    yarn install --frozen-lockfile
    yarn typecheck
    yarn test
    yarn build

The executable uses the built `dist/main.js`, so rebuilding is required after CLI source changes.

Verify the checkout directly:

    node dist/main.js resolve --help

The help must contain all three options:

    --file
    --folder
    --sdd-file

The fork does not need to expose a `specdd --version` command. Use npm package metadata plus resolver capabilities to
identify the active installation.

## 4. Link the checkout as the global `specdd`

Remove any currently installed global package, then link the development checkout:

    npm uninstall --global specdd
    cd ../specdd-cli-intended-targets
    npm link
    hash -r

Verify the active command:

    command -v specdd
    npm list --global --depth=0 specdd
    specdd resolve --help

Expected package state should identify the linked checkout as `specdd@1.2.0`.

The resolver help must expose:

    --file
    --folder
    --sdd-file

Do not rely only on the package version. The resolver flags are the capability check needed by this repository.

## 5. Smoke-test intended resolution

Return to this bridge repository.

Resolve the intended Auth target:

    specdd resolve --root tests/fixtures/specdd-two-domain --file tests/fixtures/specdd-two-domain/src/auth/future-service.ts --sections all --format json

Resolve the intended Users target:

    specdd resolve --root tests/fixtures/specdd-two-domain --file tests/fixtures/specdd-two-domain/src/users/future-identity-contract.ts --sections all --format json

Both commands must exit with status `0` without creating either target.

Confirm that an untyped missing target still fails:

    specdd resolve --root tests/fixtures/specdd-two-domain tests/fixtures/specdd-two-domain/src/auth/does-not-exist.ts --sections all --format json

That command should return a non-zero status because missing targets still require an explicit kind.

Also verify that the smoke tests did not create the intended files:

    test ! -e tests/fixtures/specdd-two-domain/src/auth/future-service.ts
    test ! -e tests/fixtures/specdd-two-domain/src/users/future-identity-contract.ts

## 6. Run the focused bridge suite

With `uv` available:

    uv run --no-project python -m unittest discover -s tests -p 'test_boundary.py'

The real-fixture intended-target tests should run rather than skip because the linked resolver exposes all three target
kind flags.

The repository bootstrap check may also be run for diagnostic purposes:

    bash scripts/bootstrap.sh --check

While the project still pins published `specdd@1.1.1`, a failure reporting that `1.1.1` is required is expected with the
linked `1.2.0` fork. Do not run bootstrap in apply mode while testing the fork because apply mode may replace the linked
checkout with the repository's pinned published package.

## 7. Development loop for the fork

When changing the CLI fork itself:

    cd ../specdd-cli-intended-targets
    git switch feature/resolve-intended-targets
    yarn install --frozen-lockfile
    yarn typecheck
    yarn test
    yarn build

Because the global package is linked to this checkout, rebuilding `dist/` makes the new implementation available through
the `specdd` command without reinstalling the package.

For the fork's full development/release checks, follow its `DEVELOPMENT.md`. If that guide still uses the repository's
aggregate build target, run:

    make build

After each rebuild, return to this bridge repository and rerun:

    specdd resolve --help
    uv run --no-project python -m unittest discover -s tests -p 'test_boundary.py'

## 8. Restore the published CLI when fork testing is finished

To stop using the development checkout:

    npm unlink --global specdd
    npm install --global specdd@1.1.1
    hash -r
    npm list --global --depth=0 specdd
    specdd resolve --help

Until upstream publishes intended-target support, the restored public `1.1.1` package is expected not to expose all
three typed resolver flags.

## Requested response

Report the output of:

    node --version
    yarn --version
    command -v specdd
    npm list --global --depth=0 specdd
    specdd resolve --help

Also report the exit status and output of:

    specdd resolve --root tests/fixtures/specdd-two-domain --file tests/fixtures/specdd-two-domain/src/auth/future-service.ts --sections all --format json
    specdd resolve --root tests/fixtures/specdd-two-domain --file tests/fixtures/specdd-two-domain/src/users/future-identity-contract.ts --sections all --format json
    specdd resolve --root tests/fixtures/specdd-two-domain tests/fixtures/specdd-two-domain/src/auth/does-not-exist.ts --sections all --format json
    uv run --no-project python -m unittest discover -s tests -p 'test_boundary.py'

If convenient, also include the result of:

    bash scripts/bootstrap.sh --check

A version-pin failure from that final command is expected while the linked `1.2.0` fork is active.
