#!/usr/bin/env bash
set -euo pipefail

readonly SPECKIT_VERSION="1.0.7"
readonly SPECKIT_TAG="v${SPECKIT_VERSION}"
readonly SPECDD_CLI_VERSION="1.1.1"
readonly SPECDD_FRAMEWORK_VERSION="1.5"
readonly MIN_NODE_MAJOR="22"
readonly ACTIVE_INTEGRATION="codex"
readonly ACTIVE_COMMANDS_DIR=".agents/skills"
readonly WORKFLOW_OVERLAY_ID="specdd-bridge"
readonly WORKFLOW_OVERLAY_SOURCE="integration/specdd/workflow-overlay.yml"
readonly WORKFLOW_OVERLAY_PRIORITY="10"
readonly MODE="${1:-apply}"

fail() {
  printf 'bootstrap: %s\n' "$*" >&2
  exit 1
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail "required command not found: ${command_name}"
}

node_major_version() {
  node -p 'Number(process.versions.node.split(".")[0])'
}

speckit_matches_pin() {
  command -v specify >/dev/null 2>&1 && specify --version 2>&1 | grep -Eq "(^|[^0-9])${SPECKIT_VERSION//./\\.}([^0-9]|$)"
}

specdd_cli_matches_pin() {
  command -v specdd >/dev/null 2>&1 && npm list --global --depth=0 "specdd@${SPECDD_CLI_VERSION}" >/dev/null 2>&1
}

specdd_framework_version() {
  if [[ ! -f .specdd/bootstrap.md ]]; then
    return 1
  fi

  awk -F: 'tolower($1) == "version" {
    value = $2
    sub(/^[[:space:]]+/, "", value)
    sub(/[[:space:]]+$/, "", value)
    print value
    exit
  }' .specdd/bootstrap.md | tr -d "\"'"
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

check_prerequisites() {
  require_command git
  require_command node
  require_command npm
  require_command uv
  require_command codex

  local node_major
  node_major="$(node_major_version)"
  if (( node_major < MIN_NODE_MAJOR )); then
    fail "Node.js ${MIN_NODE_MAJOR}+ is required by SpecDD; found $(node --version)"
  fi
}

require_skill_contains() {
  local skill_name="$1"
  local marker="$2"
  local skill_file="${ACTIVE_COMMANDS_DIR}/${skill_name}/SKILL.md"

  [[ -f "$skill_file" ]] || fail "expected Codex skill is missing: ${skill_file}"
  grep -Fq "$marker" "$skill_file" || fail "expected materialized content is missing from ${skill_file}: ${marker}"
}

check_workflow_overlay() {
  local overlay_list
  local resolved_workflow
  local step_id

  overlay_list="$(specify workflow overlay list speckit)"
  grep -Fq "$WORKFLOW_OVERLAY_ID" <<<"$overlay_list" || fail \
    "SpecDD workflow overlay is not installed: ${WORKFLOW_OVERLAY_ID}"

  resolved_workflow="$(specify workflow resolve speckit)"
  for step_id in \
    specdd-context \
    specdd-task-validation \
    specdd-authorize \
    specdd-verify
  do
    grep -Fq "$step_id" <<<"$resolved_workflow" || fail \
      "resolved Spec Kit workflow is missing structural step: ${step_id}"
  done
}

check_bridge_state() {
  [[ -d .specify/extensions/specdd ]] || fail "local SpecDD bridge extension is not installed"
  [[ -d .specify/presets/specdd-bridge ]] || fail "local SpecDD bridge preset is not installed"
  [[ -f .specify/extensions.yml ]] || fail "Spec Kit extension hook state is missing"

  require_skill_contains "speckit-specdd-context" "Build or refresh the active feature"
  require_skill_contains "speckit-specdd-validate" "Validate the active feature"
  require_skill_contains "speckit-specdd-authorize" "Authorize implementation"
  require_skill_contains "speckit-specdd-verify" "Verify actual implementation changes"

  require_skill_contains "speckit-plan" "## SpecDD Planning Augmentation"
  require_skill_contains "speckit-tasks" "## SpecDD Task Augmentation"
  require_skill_contains "speckit-converge" "## SpecDD Convergence Augmentation"

  local hook
  for hook in after_plan after_tasks before_implement after_implement; do
    grep -Fq "${hook}:" .specify/extensions.yml || fail "registered hook is missing: ${hook}"
  done

  local command_name
  for command_name in \
    speckit.specdd.context \
    speckit.specdd.validate \
    speckit.specdd.authorize \
    speckit.specdd.verify
  do
    grep -Fq "$command_name" .specify/extensions.yml || fail "registered hook command is missing: ${command_name}"
  done

  check_workflow_overlay
}

check_initialized_state() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "current directory is not a Git working tree"
  [[ -d .specify ]] || fail "Spec Kit is not initialized; run: bash scripts/bootstrap.sh"
  [[ -f .specdd/bootstrap.md ]] || fail "SpecDD is not initialized; run: bash scripts/bootstrap.sh"

  speckit_matches_pin || fail "Spec Kit ${SPECKIT_VERSION} is required; run: bash scripts/bootstrap.sh"
  specdd_cli_matches_pin || fail "npm global specdd@${SPECDD_CLI_VERSION} is required; run: bash scripts/bootstrap.sh"

  local active_integration
  active_integration="$(spec_kit_active_integration || true)"
  [[ "$active_integration" == "$ACTIVE_INTEGRATION" ]] || fail \
    "Spec Kit active integration must be '${ACTIVE_INTEGRATION}'; found '${active_integration:-unknown}'"

  [[ -d "$ACTIVE_COMMANDS_DIR" ]] || fail "Codex Spec Kit skills are missing at ${ACTIVE_COMMANDS_DIR}"

  local framework_version
  framework_version="$(specdd_framework_version || true)"
  [[ "$framework_version" == "$SPECDD_FRAMEWORK_VERSION" ]] || fail \
    "SpecDD framework ${SPECDD_FRAMEWORK_VERSION} is required; found '${framework_version:-unknown}'"

  check_bridge_state
}

run_checks() {
  check_prerequisites
  check_initialized_state

  printf '%s\n' '--- Spec Kit version ---'
  specify version
  printf '%s\n' '--- Spec Kit active integrations ---'
  specify integration list
  printf '%s\n' '--- Spec Kit extensions ---'
  specify extension list --json
  printf '%s\n' '--- Spec Kit presets ---'
  specify preset list
  printf '%s\n' '--- Spec Kit workflow overlays ---'
  specify workflow overlay list speckit
  printf '%s\n' '--- Resolved Spec Kit workflow ---'
  specify workflow resolve speckit
  printf '%s\n' '--- Spec Kit environment ---'
  specify check
  printf '%s\n' '--- SpecDD CLI package ---'
  npm list --global --depth=0 "specdd@${SPECDD_CLI_VERSION}"
  printf '%s\n' '--- SpecDD lint ---'
  specdd lint
}

install_workflow_overlay() {
  [[ -f "$WORKFLOW_OVERLAY_SOURCE" ]] || fail \
    "workflow overlay source is missing: ${WORKFLOW_OVERLAY_SOURCE}"

  specify workflow overlay remove \
    speckit \
    "$WORKFLOW_OVERLAY_ID" \
    >/dev/null 2>&1 || true

  specify workflow overlay add \
    "$WORKFLOW_OVERLAY_SOURCE" \
    --priority "$WORKFLOW_OVERLAY_PRIORITY"
}

install_bridge() {
  specify extension add integration/specdd --dev --force

  if [[ -d .specify/presets/specdd-bridge ]]; then
    specify preset remove specdd-bridge
  fi

  specify preset add --dev integration/specdd-preset --priority 10
  install_workflow_overlay
}

apply_bootstrap() {
  check_prerequisites

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git init
  fi

  if ! speckit_matches_pin; then
    uv tool install specify-cli --force --from \
      "git+https://github.com/github/spec-kit.git@${SPECKIT_TAG}"
  fi

  if ! specdd_cli_matches_pin; then
    npm install --global "specdd@${SPECDD_CLI_VERSION}"
  fi

  if [[ ! -d .specify ]]; then
    specify init --here --force --non-interactive --ignore-agent-tools \
      --script ps \
      --integration "$ACTIVE_INTEGRATION"
  else
    local active_integration
    active_integration="$(spec_kit_active_integration || true)"
    if [[ "$active_integration" != "$ACTIVE_INTEGRATION" ]]; then
      specify integration switch "$ACTIVE_INTEGRATION" --script ps
    fi
  fi

  if [[ ! -f .specdd/bootstrap.md ]]; then
    specdd init --version "$SPECDD_FRAMEWORK_VERSION"
  else
    local framework_version
    framework_version="$(specdd_framework_version || true)"
    [[ "$framework_version" == "$SPECDD_FRAMEWORK_VERSION" ]] || fail \
      "existing SpecDD framework is '${framework_version:-unknown}', expected ${SPECDD_FRAMEWORK_VERSION}; review before updating"
  fi

  install_bridge
  run_checks
}

case "$MODE" in
  apply)
    apply_bootstrap
    ;;
  --check|check)
    run_checks
    ;;
  *)
    fail "usage: bash scripts/bootstrap.sh [--check]"
    ;;
esac
