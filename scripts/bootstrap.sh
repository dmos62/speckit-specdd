#!/usr/bin/env bash
set -euo pipefail
readonly SPECKIT_VERSION="1.0.10"
readonly SPECKIT_TAG="v${SPECKIT_VERSION}"
readonly SPECDD_UPSTREAM_CLI_VERSION="1.1.1"
readonly SPECDD_COMPAT_CLI_VERSION="1.2.0"
readonly SPECDD_COMPAT_CLI_REPOSITORY="https://github.com/dmos62/specdd-cli.git"
readonly SPECDD_COMPAT_CLI_REF="feature/resolve-intended-targets"
readonly MIN_NODE_MAJOR="22"
readonly ACTIVE_INTEGRATION="codex"
readonly ACTIVE_COMMANDS_DIR=".agents/skills"
readonly WORKFLOW_OVERLAY_ID="specdd-bridge"
readonly MODE="${1:-apply}"

fail() {
  printf 'bootstrap: %s\n' "$*" >&2
  exit 1
}

require_command() {
  local command_name="$1"
  local remediation="$2"
  command -v "$command_name" >/dev/null 2>&1 || fail \
    "required command not found: ${command_name}; ${remediation}"
}

node_major_version() {
  node -p 'Number(process.versions.node.split(".")[0])'
}

speckit_matches_pin() {
  command -v specify >/dev/null 2>&1 &&
    specify --version 2>&1 |
      grep -Eq "(^|[^0-9])${SPECKIT_VERSION//./\\.}([^0-9]|$)"
}

specdd_compat_package_matches_pin() {
  command -v specdd >/dev/null 2>&1 &&
    npm list --global --depth=0 "specdd@${SPECDD_COMPAT_CLI_VERSION}" >/dev/null 2>&1
}

specdd_resolve_supports_intended_targets() {
  command -v specdd >/dev/null 2>&1 || return 1
  local help flag
  help="$(specdd resolve --help 2>&1)" || return 1
  for flag in --file --folder --sdd-file; do
    grep -Fq -- "$flag" <<<"$help" || return 1
  done
}

specdd_compat_provider_matches_pin() {
  specdd_compat_package_matches_pin &&
    specdd_resolve_supports_intended_targets
}

check_prerequisites() {
  require_command git "install Git, then rerun bash scripts/bootstrap.sh"
  require_command node "install Node.js ${MIN_NODE_MAJOR}+, then rerun bash scripts/bootstrap.sh"
  require_command npm "install npm with Node.js ${MIN_NODE_MAJOR}+, then rerun bash scripts/bootstrap.sh"
  require_command uv "install uv, then rerun bash scripts/bootstrap.sh"
  require_command codex "install the Codex CLI and put codex on PATH, then rerun bash scripts/bootstrap.sh"
  local node_major
  node_major="$(node_major_version 2>/dev/null)" ||
    fail "Node.js is present but its version could not be determined; repair Node.js and retry"
  (( node_major >= MIN_NODE_MAJOR )) ||
    fail "Node.js ${MIN_NODE_MAJOR}+ is required by SpecDD; found $(node --version)"
}

install_specdd_compat_provider() {
  local checkout package_archive source_version
  checkout="$(mktemp -d "${TMPDIR:-/tmp}/specdd-cli.XXXXXX")" ||
    fail "could not create a temporary SpecDD CLI checkout"
  if ! git clone --depth 1 --branch "$SPECDD_COMPAT_CLI_REF" "$SPECDD_COMPAT_CLI_REPOSITORY" "$checkout"; then
    rm -rf "$checkout"
    fail "could not clone temporary SpecDD resolver provider ${SPECDD_COMPAT_CLI_REPOSITORY}#${SPECDD_COMPAT_CLI_REF}"
  fi
  source_version="$(node -e 'const p=require(process.argv[1]);process.stdout.write(p.version)' "$checkout/package.json")"
  if [[ "$source_version" != "$SPECDD_COMPAT_CLI_VERSION" ]]; then
    rm -rf "$checkout"
    fail "temporary SpecDD resolver provider reports ${source_version:-unknown}; expected ${SPECDD_COMPAT_CLI_VERSION}"
  fi
  if ! (cd "$checkout" && npm ci && npm run build && npm pack --silent > .specdd-package); then
    rm -rf "$checkout"
    fail "could not build temporary SpecDD resolver provider ${SPECDD_COMPAT_CLI_REPOSITORY}#${SPECDD_COMPAT_CLI_REF}"
  fi
  package_archive="$(tail -n 1 "$checkout/.specdd-package")"
  if [[ -z "$package_archive" || ! -f "$checkout/$package_archive" ]]; then
    rm -rf "$checkout"
    fail "temporary SpecDD resolver provider build did not produce an installable npm package"
  fi
  if ! npm install --global "$checkout/$package_archive"; then
    rm -rf "$checkout"
    fail "could not install the temporary SpecDD resolver provider"
  fi
  rm -rf "$checkout"
  hash -r
  specdd_compat_package_matches_pin ||
    fail "installed SpecDD provider does not match required package version ${SPECDD_COMPAT_CLI_VERSION}"
  specdd_resolve_supports_intended_targets ||
    fail "installed SpecDD provider lacks required typed intended-target flags (--file, --folder, --sdd-file)"
}

require_skill_file() {
  local skill_name="$1"
  local skill_file="${ACTIVE_COMMANDS_DIR}/${skill_name}/SKILL.md"
  [[ -f "$skill_file" ]] || fail "expected Codex skill is missing: ${skill_file}"
}

require_skill_contains() {
  local skill_name="$1"
  local marker="$2"
  local skill_file="${ACTIVE_COMMANDS_DIR}/${skill_name}/SKILL.md"
  require_skill_file "$skill_name"
  grep -Fq "$marker" "$skill_file" ||
    fail "expected materialized content is missing from ${skill_file}: ${marker}"
}

check_workflow_overlay() {
  local overlay_list resolved_workflow step_id
  overlay_list="$(specify workflow overlay list speckit 2>&1)" ||
    fail "Spec Kit could not inspect workflow overlays: ${overlay_list}"
  grep -Fq "$WORKFLOW_OVERLAY_ID" <<<"$overlay_list" ||
    fail "SpecDD workflow overlay is not installed: ${WORKFLOW_OVERLAY_ID}"
  resolved_workflow="$(specify workflow resolve speckit 2>&1)" ||
    fail "Spec Kit could not resolve the speckit workflow: ${resolved_workflow}"
  for step_id in specdd-context specdd-task-validation specdd-authorize specdd-verify; do
    grep -Fq "$step_id" <<<"$resolved_workflow" ||
      fail "resolved Spec Kit workflow is missing structural step: ${step_id}"
  done
}

check_bridge_state() {
  [[ -d .specify/extensions/specdd ]] || fail "local SpecDD bridge extension is not installed"
  [[ -d .specify/presets/specdd-bridge ]] || fail "local SpecDD bridge preset is not installed"
  [[ -f .specify/extensions.yml ]] || fail "Spec Kit extension hook state is missing"
  local skill_name
  for skill_name in \
    speckit-specdd-context \
    speckit-specdd-validate \
    speckit-specdd-authorize \
    speckit-specdd-verify
  do
    require_skill_file "$skill_name"
  done
  require_skill_contains "speckit-plan" "## SpecDD Planning Augmentation"
  require_skill_contains "speckit-tasks" "## SpecDD Task Augmentation"
  require_skill_contains "speckit-converge" "## SpecDD Convergence Augmentation"
  local hook command_name
  for hook in after_plan after_tasks before_implement after_implement; do
    grep -Fq "${hook}:" .specify/extensions.yml ||
      fail "registered hook is missing: ${hook}"
  done
  for command_name in \
    speckit.specdd.context \
    speckit.specdd.validate \
    speckit.specdd.authorize \
    speckit.specdd.verify
  do
    grep -Fq "$command_name" .specify/extensions.yml ||
      fail "registered hook command is missing: ${command_name}"
  done
  check_workflow_overlay
}

check_initialized_state() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    fail "current directory is not a Git working tree"
  [[ -d .specify ]] ||
    fail "Spec Kit is not initialized; run: bash scripts/bootstrap.sh"
  command -v specify >/dev/null 2>&1 ||
    fail "Spec Kit CLI 'specify' is not installed; run: bash scripts/bootstrap.sh"
  command -v specdd >/dev/null 2>&1 ||
    fail "SpecDD CLI 'specdd' is not installed; run: bash scripts/bootstrap.sh"
  speckit_matches_pin ||
    fail "Spec Kit ${SPECKIT_VERSION} is required; run: bash scripts/bootstrap.sh"
  specdd_compat_package_matches_pin || fail \
    "temporary typed-target provider specdd ${SPECDD_COMPAT_CLI_VERSION} is required while upstream ${SPECDD_UPSTREAM_CLI_VERSION} lacks intended-target resolution; run: bash scripts/bootstrap.sh"
  specdd_resolve_supports_intended_targets || fail \
    "installed SpecDD provider lacks the typed intended-target flag set (--file, --folder, --sdd-file); run bash scripts/bootstrap.sh to repair it"
  local active_integration
  active_integration="$(spec_kit_active_integration || true)"
  [[ "$active_integration" == "$ACTIVE_INTEGRATION" ]] ||
    fail "Spec Kit active integration must be '${ACTIVE_INTEGRATION}'; found '${active_integration:-unknown}'"
  [[ -d "$ACTIVE_COMMANDS_DIR" ]] ||
    fail "Codex Spec Kit skills are missing at ${ACTIVE_COMMANDS_DIR}"
  check_bridge_state
}

spec_kit_active_integration() {
  [[ -f .specify/integration.json ]] || return 1
  node -e '
const fs = require("fs");
try {
  const state = JSON.parse(fs.readFileSync(".specify/integration.json", "utf8"));
  const value = state.default_integration || state.integration;
  if (typeof value !== "string" || value.length === 0) process.exit(1);
  process.stdout.write(value);
} catch {
  process.exit(1);
}
'
}

run_checks() {
  check_prerequisites
  printf '%s\n' '--- Runtime versions ---'
  printf '%s' 'Node.js: '; node --version
  printf '%s' 'Python: '; uv run --no-project python --version
  check_initialized_state
  printf '%s\n' '--- Spec Kit version ---'; specify version
  printf '%s\n' '--- Spec Kit active integrations ---'; specify integration list
  printf '%s\n' '--- Spec Kit extensions ---'; specify extension list --json
  printf '%s\n' '--- Spec Kit presets ---'; specify preset list
  printf '%s\n' '--- Spec Kit workflow overlays ---'; specify workflow overlay list speckit
  printf '%s\n' '--- Resolved Spec Kit workflow ---'; specify workflow resolve speckit
  printf '%s\n' '--- Spec Kit environment ---'; specify check
  printf '%s\n' "--- SpecDD stable upstream CLI baseline: ${SPECDD_UPSTREAM_CLI_VERSION} ---"
  printf '%s\n' '--- Temporary typed-target provider ---'
  npm list --global --depth=0 "specdd@${SPECDD_COMPAT_CLI_VERSION}"
  printf '%s\n' '--- SpecDD resolve capabilities ---'; specdd resolve --help
  printf '%s\n' '--- SpecDD lint ---'; specdd lint
}

install_bridge() {
  bash scripts/install.sh --source .
}

apply_bootstrap() {
  check_prerequisites
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || git init
  if ! speckit_matches_pin; then
    uv tool install specify-cli --force \
      --from "git+https://github.com/github/spec-kit.git@${SPECKIT_TAG}"
  fi
  specdd_compat_provider_matches_pin || install_specdd_compat_provider
  if [[ ! -d .specify ]]; then
    specify init \
      --here \
      --force \
      --non-interactive \
      --ignore-agent-tools \
      --script ps \
      --integration "$ACTIVE_INTEGRATION"
  else
    local active_integration
    active_integration="$(spec_kit_active_integration || true)"
    [[ "$active_integration" == "$ACTIVE_INTEGRATION" ]] ||
      specify integration switch "$ACTIVE_INTEGRATION" --script ps
  fi
  install_bridge
  run_checks
}

case "$MODE" in
  apply) apply_bootstrap ;;
  --check|check) run_checks ;;
  *) fail "usage: bash scripts/bootstrap.sh [--check]" ;;
esac
