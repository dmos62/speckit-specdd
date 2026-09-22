# Human Request: Use the Intended-Target SpecDD CLI Fork

The bridge's intended-target work is implemented on a temporary SpecDD CLI fork, but the feature is not yet available
through a published upstream `specdd` release.

Set up the fork as the locally active `specdd` executable so the bridge can exercise the implemented `--file`,
`--folder`, and `--sdd-file` resolver behavior.

Fork:

- Repository: https://github.com/dmos62/specdd-cli
- Branch: `feature/resolve-intended-targets`
- Usage reference:
  https://github.com/dmos62/specdd-cli/blob/feature/resolve-intended-targets/README.md
- Development reference:
  https://github.com/dmos62/specdd-cli/blob/feature/resolve-intended-targets/DEVELOPMENT.md

The fork intentionally still reports package version `1.1.1`. Do not update this repository's compatibility pin merely
to distinguish the fork from the published package.

## 1. Install host prerequisites

The CLI requires Node.js 22 or newer. The fork declares Yarn `1.22.22`.

The bridge checks also require `uv`, Git, npm, and the Codex CLI.

Confirm the important tools:

    node --version
    npm --version
    git --version
    uv --version
    codex --version

Install Yarn 1.22.22 if it is not already available:

    npm install --global yarn@1.22.22
    yarn --version

The expected Yarn version is `1.22.22`.

## 2. Clone and build the fork

Keep the CLI checkout outside this repository.

For example:

    cd ..
    git clone --branch feature/resolve-intended-targets https://github.com/dmos62/specdd-cli.git specdd-cli-intended-targets
    cd specdd-cli-intended-targets
    git status
    git branch --show-current
    yarn install --frozen-lockfile
    yarn typecheck
    yarn test
    yarn build

The active branch should be:

    feature/resolve-intended-targets

The package requires a build because its executable is `dist/main.js`.

A direct smoke check from the checkout should succeed:

    node dist/main.js resolve --help

Confirm that the help includes all three options:

    --file
    --folder
    --sdd-file

## 3. Link the development checkout as the global `specdd`

Remove the currently installed global package, then link the built checkout:

    npm uninstall --global specdd
    cd ../specdd-cli-intended-targets
    npm link
    hash -r

Confirm which executable is active:

    command -v specdd
    npm list --global --depth=0 specdd
    specdd resolve --help

The resolver help must contain all three intended-target flags. The package version alone is not sufficient evidence
because both the public package and this fork currently report `1.1.1`.

## 4. Smoke-test intended resolution

From this bridge repository, run:

    specdd resolve --root tests/fixtures/specdd-two-domain --file tests/fixtures/specdd-two-domain/src/auth/future-service.ts --sections all --format json

Then test the intended Users contract:

    specdd resolve --root tests/fixtures/specdd-two-domain --file tests/fixtures/specdd-two-domain/src/users/future-identity-contract.ts --sections all --format json

Both commands should exit with status `0` without creating either target.

Also confirm the untyped missing-target behavior remains conservative:

    specdd resolve --root tests/fixtures/specdd-two-domain tests/fixtures/specdd-two-domain/src/auth/does-not-exist.ts --sections all --format json

That command should fail because a missing target without an explicit kind still requires an existing path.

## 5. Run this repository's checks

From the bridge repository:

    bash scripts/bootstrap.sh --check

Then run the focused boundary suite:

    uv run --no-project python -m unittest discover -s tests -p 'test_boundary.py'

The real-fixture intended-target tests should run rather than skip because the linked resolver exposes all three typed
target flags.

If `bash scripts/bootstrap.sh` is run in apply mode later, re-check `specdd resolve --help` afterward. The temporary
fork and the published package share version `1.1.1`, so resolver capabilities are the definitive check that the desired
CLI is active.

## 6. Development loop for the fork

When changing the fork itself:

    cd ../specdd-cli-intended-targets
    git switch feature/resolve-intended-targets
    yarn install --frozen-lockfile
    yarn typecheck
    yarn test
    yarn build

Because `npm link` points the global package at this checkout, rebuilding `dist/` makes the updated CLI available through
the global `specdd` command without reinstalling it.

For the fork's complete release-preparation checks, its development guide uses:

    make build

After rebuilding, return to this repository and rerun:

    specdd resolve --help
    uv run --no-project python -m unittest discover -s tests -p 'test_boundary.py'
    bash scripts/bootstrap.sh --check

## 7. Restore the published CLI when needed

To stop using the fork:

    npm unlink --global specdd
    npm install --global specdd@1.1.1
    hash -r
    specdd resolve --help

Until an upstream release containing intended-target resolution is published, the restored public `1.1.1` package is
expected not to expose `--file`, `--folder`, and `--sdd-file`.

## Requested result

After setup, report these outputs so bridge work can continue against the intended-target implementation:

    node --version
    yarn --version
    command -v specdd
    npm list --global --depth=0 specdd
    specdd resolve --help
    bash scripts/bootstrap.sh --check
    uv run --no-project python -m unittest discover -s tests -p 'test_boundary.py'


----------

Response: specdd cli fork is setup and version bumped to 1.2.0.

````
$ command -v specdd
specdd --version
specdd resolve --help
npm list --global --depth=0 specdd
/c/Users/Domas/AppData/Roaming/npm/specdd
error: unknown option '--version'
Usage: specdd resolve [options] <target>

Resolve relevant SpecDD specs for a target path.

Arguments:
  target              Directory, .sdd file, or ordinary file to resolve.

Options:
  --root <path>       Root directory for resolution. Defaults to the current directory.
  --file              Treat the target as an intended ordinary file.
  --folder            Treat the target as an intended directory.
  --sdd-file          Treat the target as an intended .sdd specification file.
  --section <name>    Section to include, or all. May be repeated. (default: [])
  --sections <names>  Comma-separated sections to include, or all.
  --depth <depth>     Soft-link expansion depth: non-negative integer or all. (default:
                      "2")
  --format <format>   Output format: text, json, or json-extended. (default: "text")
  -h, --help          display help for command
Target kind options are mutually exclusive. They allow resolution before a target exists and are normally unnecessary for existing targets.

Copyright (c) 2026 Matīss Treinis and SpecDD contributors
Spec help: https://specdd.ai
CLI help: https://github.com/specdd/cli
C:\Users\Domas\AppData\Roaming\npm
└── specdd@1.2.0 -> .\..\..\..\projektai\specdd-cli
````

