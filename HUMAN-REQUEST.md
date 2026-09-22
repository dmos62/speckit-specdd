# Human Request: Install the Intended-Target SpecDD CLI Fork

The intended-path resolver work is implemented on a pre-release SpecDD CLI fork:

- Repository: https://github.com/dmos62/specdd-cli
- Branch: `feature/resolve-intended-targets`
- Package name/version on the branch: `specdd@1.1.1`

Set up this fork on the development host so this repository can exercise the new `specdd resolve --file`, `--folder`,
and `--sdd-file` behavior before an upstream package release exists.

Do not change this repository's SpecDD CLI compatibility pin yet. The fork intentionally still reports version `1.1.1`;
the bridge should continue using that pin until a deliberate released-version compatibility update is performed.

## 1. Install the host prerequisites

The current repository check stops because `node` is missing. Install Node.js 22 or newer using the host's preferred
Node installation method.

Then verify Node and npm:

    node --version
    npm --version

Install the Yarn version declared by the SpecDD CLI repository:

    npm install --global yarn@1.22.22
    yarn --version

The expected Yarn version is `1.22.22`.

## 2. Clone the fork beside this repository

From this repository root:

    BRIDGE_ROOT="$(git rev-parse --show-toplevel)"
    FORK_DIR="${SPECDD_CLI_FORK_DIR:-$(dirname "$BRIDGE_ROOT")/specdd-cli-intended-targets}"

    git clone \
      --branch feature/resolve-intended-targets \
      --single-branch \
      https://github.com/dmos62/specdd-cli.git \
      "$FORK_DIR"

If that checkout already exists, update it without discarding local work:

    git -C "$FORK_DIR" fetch origin feature/resolve-intended-targets
    git -C "$FORK_DIR" switch feature/resolve-intended-targets
    git -C "$FORK_DIR" pull --ff-only origin feature/resolve-intended-targets

Keep the fork outside this repository so its build output and dependencies do not become bridge project state.

## 3. Install, verify, and build the fork

Run:

    cd "$FORK_DIR"
    yarn install --frozen-lockfile
    yarn typecheck
    yarn test
    yarn build

For the fork's full contributor/release-preparation check, `make build` is also available. It performs additional audit,
packaging, and generated-metadata checks and is useful before upstreaming further CLI changes.

The fork's development documentation is:

https://github.com/dmos62/specdd-cli/blob/feature/resolve-intended-targets/DEVELOPMENT.md

## 4. Install a stable local build for bridge usage

For ordinary bridge work, install a packed build instead of linking the working tree:

    cd "$FORK_DIR"
    PACKAGE_DIR="$(mktemp -d)"
    TARBALL="$(npm pack --silent --pack-destination "$PACKAGE_DIR")"
    npm install --global "$PACKAGE_DIR/$TARBALL"
    rm -rf "$PACKAGE_DIR"
    hash -r

Verify that npm sees the package at the bridge's existing compatibility version:

    npm list --global --depth=0 specdd@1.1.1

Version output alone is not enough to distinguish the fork from the published `1.1.1`; verify the new behavior as well:

    specdd resolve --help

The help output must contain all three options:

    --file
    --folder
    --sdd-file

## 5. Smoke-test intended-target resolution

Return to this repository and run the resolver against missing paths in the existing two-domain fixture:

    cd "$BRIDGE_ROOT"
    FIXTURE_ROOT="$BRIDGE_ROOT/tests/fixtures/specdd-two-domain"

    specdd resolve \
      --root "$FIXTURE_ROOT" \
      --file "$FIXTURE_ROOT/src/auth/missing.ts" \
      --sections all \
      --format json

    specdd resolve \
      --root "$FIXTURE_ROOT" \
      --folder "$FIXTURE_ROOT/src/auth/missing-domain" \
      --sections all \
      --format json

    specdd resolve \
      --root "$FIXTURE_ROOT" \
      --sdd-file "$FIXTURE_ROOT/src/auth/missing-service.sdd" \
      --sections all \
      --format json

All three commands must exit with status `0`. They must resolve existing governing context without creating any of those
targets or their missing directories.

Confirm no probe artifacts appeared:

    test ! -e "$FIXTURE_ROOT/src/auth/missing.ts"
    test ! -e "$FIXTURE_ROOT/src/auth/missing-domain"
    test ! -e "$FIXTURE_ROOT/src/auth/missing-service.sdd"

The fork README documents the intended-target behavior here:

https://github.com/dmos62/specdd-cli/blob/feature/resolve-intended-targets/README.md

## 6. Run the bridge environment check

From this repository root:

    cd "$BRIDGE_ROOT"
    bash scripts/bootstrap.sh --check

If the check reports another missing host dependency such as `uv` or `codex`, follow the dependency-specific remediation
printed by the bootstrap script and rerun the check.

Do not run a command that deliberately reinstalls the public `specdd@1.1.1` over the fork while intended-target bridge
work is in progress.

## Development mode

When actively changing the CLI fork, a global npm link is more convenient than repeatedly packing it.

After the initial dependency installation:

    cd "$FORK_DIR"
    yarn build
    npm link
    hash -r
    npm list --global --depth=0 specdd

After TypeScript changes, rebuild before exercising the global command:

    yarn typecheck
    yarn test
    yarn build

The linked `specdd` executable uses `dist/main.js`, so rebuilding updates the executable behavior without another
`npm link`.

When development-link behavior is no longer wanted, reinstall the packed fork using step 4. Do not restore the public
registry package until the bridge no longer needs the fork or an upstream release containing intended-target resolution
has replaced it.

## Report back

Provide the output or relevant result of:

- `node --version`
- `yarn --version`
- `npm list --global --depth=0 specdd@1.1.1`
- confirmation that `specdd resolve --help` contains all three intended-target flags
- confirmation that the three missing-target smoke tests exit successfully without creating files or directories
- `bash scripts/bootstrap.sh --check`

Once these checks succeed, the bridge TODO can proceed with resolver-backed intended-path integration and focused parity
tests against the fork.

-------

Response:

````
$ bash scripts/bootstrap.sh --check
--- Runtime versions ---
Node.js: v22.14.0
Python: Python 3.12.11
--- Spec Kit version ---
                         ███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗                          
                         ██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝                          
                         ███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝                           
                         ╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝                            
                         ███████║██║     ███████╗╚██████╗██║██║        ██║                             
                         ╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝                             
                                                                                                       
                           GitHub Spec Kit - Spec-Driven Development Toolkit                           

╭────────────────────────────────────── Specify CLI Information ──────────────────────────────────────╮│                                                                                                     ││     CLI Version    1.0.7                                                                            ││                                                                                                     ││          Python    3.12.11                                                                          ││        Platform    Windows                                                                          ││    Architecture    AMD64                                                                            ││      OS Version    10.0.19045                                                                       ││                                                                                                     │╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
--- Spec Kit active integrations ---
                                       Coding Agent Integrations                                       
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓┃ Key          ┃ Name                       ┃ Status              ┃ CLI Required ┃ Multi-install Safe ┃┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩│ agy          │ Antigravity                │                     │ yes          │ no                 ││ alquimia     │ Alquimia AI                │                     │ yes          │ yes                ││ amp          │ Amp                        │                     │ yes          │ no                 ││ auggie       │ Auggie CLI                 │                     │ yes          │ yes                ││ bob          │ IBM Bob                    │                     │ no (IDE)     │ no                 ││ claude       │ Claude Code                │                     │ yes          │ yes                ││ cline        │ Cline                      │                     │ no (IDE)     │ yes                ││ codebuddy    │ CodeBuddy                  │                     │ yes          │ yes                ││ codex        │ Codex CLI                  │ installed (default) │ yes          │ yes                ││ command-code │ Command Code               │                     │ yes          │ yes                ││ copilot      │ GitHub Copilot             │                     │ no (IDE)     │ no                 ││ cursor-agent │ Cursor                     │                     │ no (IDE)     │ yes                ││ devin        │ Devin for Terminal         │                     │ yes          │ no                 ││ docker-agent │ Docker Agent               │                     │ yes          │ no                 ││ droid        │ Factory Droid              │                     │ yes          │ yes                ││ dsh          │ DeepSeek Harness           │                     │ yes          │ yes                ││ firebender   │ Firebender                 │                     │ no (IDE)     │ yes                ││ forge        │ Forge                      │                     │ yes          │ no                 ││ gemini       │ Gemini CLI                 │                     │ yes          │ yes                ││ generic      │ Generic (bring your own    │                     │ no (IDE)     │ no                 ││              │ agent)                     │                     │              │                    ││ goose        │ Goose                      │                     │ yes          │ no                 ││ grok         │ Grok Build                 │                     │ yes          │ yes                ││ hermes       │ Hermes Agent               │                     │ yes          │ no                 ││ junie        │ Junie                      │                     │ yes          │ yes                ││ kilocode     │ Kilo Code                  │                     │ no (IDE)     │ yes                ││ kimi         │ Kimi Code                  │                     │ yes          │ no                 ││ kiro-cli     │ Kiro CLI                   │                     │ yes          │ yes                ││ lingma       │ Lingma                     │                     │ no (IDE)     │ yes                ││ muse         │ Muse Code                  │                     │ yes          │ no                 ││ omp          │ Oh My Pi                   │                     │ yes          │ yes                ││ opencode     │ opencode                   │                     │ yes          │ no                 ││ pi           │ Pi Coding Agent            │                     │ yes          │ yes                ││ qodercli     │ Qoder CLI                  │                     │ yes          │ yes                ││ qwen         │ Qwen Code                  │                     │ yes          │ yes                ││ rovodev      │ RovoDev ACLI               │                     │ yes          │ no                 ││ shai         │ SHAI                       │                     │ yes          │ yes                ││ tabnine      │ Tabnine CLI                │                     │ yes          │ yes                ││ trae         │ Trae                       │                     │ no (IDE)     │ yes                ││ vibe         │ Mistral Vibe               │                     │ yes          │ yes                ││ zcode        │ ZCode                      │                     │ yes          │ yes                ││ zed          │ Zed                        │                     │ no (IDE)     │ no                 │└──────────────┴────────────────────────────┴─────────────────────┴──────────────┴────────────────────┘
Default integration: codex
Installed integrations: codex
--- Spec Kit extensions ---
[{"id": "specdd", "name": "SpecDD Bridge", "description": "Project SpecDD authority into Spec Kit feature workflows without duplicating persistent system contracts.", "version": "0.1.0", "author": "SpecDD contributors", "priority": 10, "enabled": true, "source": {"kind": "local"}, "provides": {"commands": 4, "templates": 0, "scripts": 0, "hooks": 4}}]
--- Spec Kit presets ---

Installed Presets (in resolution order — highest precedence first)

  SpecDD Bridge Workflow (specdd-bridge) v0.1.0 — enabled — priority 10
    Augment Spec Kit planning, tasks, and convergence with current SpecDD authority context.
    Tags: specdd, architecture, workflow
    Templates: 3

Lower priority number = higher precedence. Ties are broken by preset id (alphabetical).
--- Spec Kit workflow overlays ---
Overlays for workflow 'speckit':
  • specdd-bridge (priority=10, source=project:specdd-bridge, enabled)
--- Resolved Spec Kit workflow ---
Resolved workflow 'speckit':
Layers (highest precedence first):
  • [project-overlay] project:specdd-bridge (priority=10)
  • [base] base (priority=n/a)
Step attribution:
  • specify: base
  • review-spec: base
  • plan: base
  • specdd-context: project:specdd-bridge
  • review-plan: base
  • tasks: base
  • specdd-task-validation: project:specdd-bridge
  • specdd-authorize: project:specdd-bridge
  • implement: base
  • specdd-verify: project:specdd-bridge
--- Spec Kit environment ---
                         ███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗                          
                         ██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝                          
                         ███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝                           
                         ╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝                            
                         ███████║██║     ███████╗╚██████╗██║██║        ██║                             
                         ╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝                             
                                                                                                       
                           GitHub Spec Kit - Spec-Driven Development Toolkit                           

Checking for installed tools...

Check Available Tools
├── ● Antigravity (not found)
├── ● Alquimia AI (not found)
├── ● Amp (not found)
├── ● Auggie CLI (not found)
├── ○ IBM Bob (IDE-based, no CLI check)
├── ● Claude Code (not found)
├── ○ Cline (IDE-based, no CLI check)
├── ● CodeBuddy (not found)
├── ● Codex CLI (available)
├── ● Command Code (not found)
├── ○ GitHub Copilot (IDE-based, no CLI check)
├── ○ Cursor (IDE-based, no CLI check)
├── ● Devin for Terminal (not found)
├── ● Docker Agent (not found)
├── ● Factory Droid (not found)
├── ● DeepSeek Harness (not found)
├── ○ Firebender (IDE-based, no CLI check)
├── ● Forge (not found)
├── ● Gemini CLI (not found)
├── ● Goose (not found)
├── ● Grok Build (not found)
├── ● Hermes Agent (not found)
├── ● Junie (not found)
├── ○ Kilo Code (IDE-based, no CLI check)
├── ● Kimi Code (not found)
├── ● Kiro CLI (not found)
├── ○ Lingma (IDE-based, no CLI check)
├── ● Muse Code (not found)
├── ● Oh My Pi (not found)
├── ● opencode (not found)
├── ● Pi Coding Agent (not found)
├── ● Qoder CLI (not found)
├── ● Qwen Code (not found)
├── ● RovoDev ACLI (not found)
├── ● SHAI (not found)
├── ● Tabnine CLI (not found)
├── ○ Trae (IDE-based, no CLI check)
├── ● Mistral Vibe (not found)
├── ● ZCode (not found)
├── ○ Zed (IDE-based, no CLI check)
├── ● Visual Studio Code (available)
└── ● Visual Studio Code Insiders (not found)

Specify CLI is ready to use!
Tip: Run 'specify self check' to verify you have the latest CLI version
--- SpecDD CLI package ---
C:\Users\Domas\AppData\Roaming\npm
└── specdd@1.1.1

--- SpecDD lint ---
0 errors, 0 warnings in 36 specs

[13:15] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ node --version
v22.14.0

[13:45] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ yarn --version
1.22.22

[13:45] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ npm list --global --depth=0 specdd@1.1.1
C:\Users\Domas\AppData\Roaming\npm
└── specdd@1.1.1


[13:45] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ specdd resolve --help
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
  --depth <depth>     Soft-link expansion depth: non-negative integer or all. (default: "2")
  --format <format>   Output format: text, json, or json-extended. (default: "text")
  -h, --help          display help for command
Target kind options are mutually exclusive. They allow resolution before a target exists and are normally unnecessary for existing targets.

Copyright (c) 2026 Matīss Treinis and SpecDD contributors
Spec help: https://specdd.ai
CLI help: https://github.com/specdd/cli
````

> - confirmation that the three missing-target smoke tests exit successfully without creating files or directories

Yes.