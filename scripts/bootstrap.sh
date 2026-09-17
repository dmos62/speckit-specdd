#!/usr/bin/env bash
set -euo pipefail

readonly SPECKIT_VERSION="1.0.7"
readonly SPECKIT_TAG="v${SPECKIT_VERSION}"
readonly SPECDD_CLI_VERSION="1.1.1"
readonly SPECDD_FRAMEWORK_VERSION="1.5"
readonly MIN_NODE_MAJOR="22"
readonly GENERIC_COMMANDS_DIR=".specify-agent/commands"
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

check_prerequisites() {
  require_command git
  require_command node
  require_command npm
  require_command uv

  local node_major
  node_major="$(node_major_version)"
  if (( node_major < MIN_NODE_MAJOR )); then
    fail "Node.js ${MIN_NODE_MAJOR}+ is required by SpecDD; found $(node --version)"
  fi
}

check_initialized_state() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "current directory is not a Git working tree"
  [[ -d .specify ]] || fail "Spec Kit is not initialized; run: bash scripts/bootstrap.sh"
  [[ -d "$GENERIC_COMMANDS_DIR" ]] || fail "Spec Kit generic integration commands are missing at ${GENERIC_COMMANDS_DIR}"
  [[ -f .specdd/bootstrap.md ]] || fail "SpecDD is not initialized; run: bash scripts/bootstrap.sh"

  speckit_matches_pin || fail "Spec Kit ${SPECKIT_VERSION} is required; run: bash scripts/bootstrap.sh"
  specdd_cli_matches_pin || fail "npm global specdd@${SPECDD_CLI_VERSION} is required; run: bash scripts/bootstrap.sh"

  local framework_version
  framework_version="$(specdd_framework_version || true)"
  [[ "$framework_version" == "$SPECDD_FRAMEWORK_VERSION" ]] || fail \
    "SpecDD framework ${SPECDD_FRAMEWORK_VERSION} is required; found '${framework_version:-unknown}'"
}

run_checks() {
  check_prerequisites
  check_initialized_state

  printf '%s\n' '--- Spec Kit version ---'
  specify version
  printf '%s\n' '--- Spec Kit environment ---'
  specify check
  printf '%s\n' '--- SpecDD CLI package ---'
  npm list --global --depth=0 "specdd@${SPECDD_CLI_VERSION}"
  printf '%s\n' '--- SpecDD lint ---'
  specdd lint
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
      --integration generic \
      --integration-options="--commands-dir ${GENERIC_COMMANDS_DIR}"
  fi

  if [[ ! -f .specdd/bootstrap.md ]]; then
    specdd init --version "$SPECDD_FRAMEWORK_VERSION"
  else
    local framework_version
    framework_version="$(specdd_framework_version || true)"
    [[ "$framework_version" == "$SPECDD_FRAMEWORK_VERSION" ]] || fail \
      "existing SpecDD framework is '${framework_version:-unknown}', expected ${SPECDD_FRAMEWORK_VERSION}; review before updating"
  fi

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
