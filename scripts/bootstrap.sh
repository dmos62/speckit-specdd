#!/usr/bin/env bash
set -euo pipefail
readonly SPECKIT_VERSION="1.0.10"
readonly SPECKIT_TAG="v${SPECKIT_VERSION}"
readonly ACTIVE_INTEGRATION="codex"
readonly ACTIVE_COMMANDS_DIR=".agents/skills"
readonly BOUNDARY_EXTENSION_ID="boundary"
readonly BOUNDARY_PRESET_ID="boundary"
readonly WORKFLOW_OVERLAY_ID="boundary"
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

speckit_matches_pin() {
  command -v specify >/dev/null 2>&1 &&
    specify --version 2>&1 |
      grep -Eq "(^|[^0-9])${SPECKIT_VERSION//./\\.}([^0-9]|$)"
}

check_prerequisites() {
  require_command git "install Git, then rerun bash scripts/bootstrap.sh"
  require_command uv "install uv, then rerun bash scripts/bootstrap.sh"
  require_command codex "install the Codex CLI and put codex on PATH, then rerun bash scripts/bootstrap.sh"
}

require_skill_file() {
  local skill_name="$1"
  local skill_file="${ACTIVE_COMMANDS_DIR}/${skill_name}/SKILL.md"
  [[ -f "$skill_file" ]] ||
    fail "expected Codex skill is missing: ${skill_file}"
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
    fail "Boundary workflow overlay is not installed: ${WORKFLOW_OVERLAY_ID}"

  resolved_workflow="$(specify workflow resolve speckit 2>&1)" ||
    fail "Spec Kit could not resolve the speckit workflow: ${resolved_workflow}"
  for step_id in boundary-authorize boundary-verify; do
    grep -Fq "$step_id" <<<"$resolved_workflow" ||
      fail "resolved Spec Kit workflow is missing structural step: ${step_id}"
  done
}

check_adapter_state() {
  [[ -d ".specify/extensions/${BOUNDARY_EXTENSION_ID}" ]] ||
    fail "Boundary Spec Kit adapter extension is not installed"
  [[ -d ".specify/presets/${BOUNDARY_PRESET_ID}" ]] ||
    fail "Boundary task preset is not installed"
  [[ -f .specify/boundary-runtime/boundary/__init__.py ]] ||
    fail "generated Boundary runtime is missing"

  local skill_name
  for skill_name in \
    speckit-boundary-authorize \
    speckit-boundary-verify \
    boundary-scope \
    boundary-implement \
    boundary-contracts
  do
    require_skill_file "$skill_name"
  done

  require_skill_contains "speckit-tasks" "## Boundary Write Scope"
  check_workflow_overlay
}

spec_kit_active_integration() {
  [[ -f .specify/integration.json ]] || return 1
  uv run --no-project python - .specify/integration.json <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        state = json.load(handle)
except (OSError, ValueError):
    raise SystemExit(1)

value = state.get("default_integration") or state.get("integration")
if not isinstance(value, str) or not value:
    raise SystemExit(1)
print(value)
PY
}

check_initialized_state() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    fail "current directory is not a Git working tree"
  [[ -d .specify ]] ||
    fail "Spec Kit is not initialized; run: bash scripts/bootstrap.sh"
  command -v specify >/dev/null 2>&1 ||
    fail "Spec Kit CLI 'specify' is not installed; run: bash scripts/bootstrap.sh"
  speckit_matches_pin ||
    fail "Spec Kit ${SPECKIT_VERSION} is required; run: bash scripts/bootstrap.sh"

  local active_integration
  active_integration="$(spec_kit_active_integration || true)"
  [[ "$active_integration" == "$ACTIVE_INTEGRATION" ]] ||
    fail "Spec Kit active integration must be '${ACTIVE_INTEGRATION}'; found '${active_integration:-unknown}'"
  [[ -d "$ACTIVE_COMMANDS_DIR" ]] ||
    fail "Codex Spec Kit skills are missing at ${ACTIVE_COMMANDS_DIR}"

  check_adapter_state
}

run_checks() {
  check_prerequisites
  printf '%s\n' '--- Runtime versions ---'
  printf '%s' 'Python: '; uv run --no-project python --version
  check_initialized_state
  printf '%s\n' '--- Spec Kit version ---'; specify version
  printf '%s\n' '--- Spec Kit active integrations ---'; specify integration list
  printf '%s\n' '--- Spec Kit extensions ---'; specify extension list --json
  printf '%s\n' '--- Spec Kit presets ---'; specify preset list
  printf '%s\n' '--- Spec Kit workflow overlays ---'; specify workflow overlay list speckit
  printf '%s\n' '--- Resolved Spec Kit workflow ---'; specify workflow resolve speckit
  printf '%s\n' '--- Spec Kit environment ---'; specify check
}

install_adapter() {
  bash scripts/install.sh --source .
}

apply_bootstrap() {
  check_prerequisites
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || git init

  if ! speckit_matches_pin; then
    uv tool install specify-cli --force \
      --from "git+https://github.com/github/spec-kit.git@${SPECKIT_TAG}"
  fi

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

  install_adapter
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
