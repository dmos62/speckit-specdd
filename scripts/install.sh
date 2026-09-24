#!/usr/bin/env bash
set -euo pipefail
readonly SPECKIT_VERSION="1.0.10"
readonly ACTIVE_INTEGRATION="codex"
readonly EXTENSION_ID="boundary"
readonly PRESET_ID="boundary"
readonly WORKFLOW_ID="speckit"
readonly WORKFLOW_OVERLAY_ID="boundary"
readonly WORKFLOW_OVERLAY_PRIORITY="10"
readonly CODEX_SKILL_ADAPTER="adapters/codex/materialize.py"
readonly BOUNDARY_RUNTIME_DIR=".specify/boundary-runtime"
readonly INSTALL_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

ACTION="install"
SOURCE="."
TEMP_ROOT=""
SOURCE_ROOT=""

fail() {
  printf 'install: %s\n' "$*" >&2
  exit 1
}

source "$INSTALL_SCRIPT_DIR/install-source.sh"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install.sh [--source <directory|archive|immutable-github-url>]
  bash scripts/install.sh --check
  bash scripts/install.sh --remove

Install sources:
  A local repository/package directory.
  A local .zip, .tar.gz, or .tgz archive.
  An immutable GitHub tag, commit, or release archive URL.

Mutable GitHub branch archives are intentionally rejected.
EOF
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 ||
    fail "required command not found: ${command_name}"
}

speckit_matches_pin() {
  specify --version 2>&1 |
    grep -Eq "(^|[^0-9])${SPECKIT_VERSION//./\\.}([^0-9]|$)"
}

check_install_prerequisites() {
  require_command specify
  require_command uv
  require_command codex
  speckit_matches_pin ||
    fail "Spec Kit ${SPECKIT_VERSION} is required"
}

active_integration() {
  [[ -f .specify/integration.json ]] || return 1
  uv run --no-project python - .specify/integration.json <<'PY'
import json
import sys

try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError):
    raise SystemExit(1)

value = data.get("default_integration") or data.get("integration")
if not isinstance(value, str) or not value:
    raise SystemExit(1)
print(value)
PY
}

ensure_codex_project() {
  if [[ ! -d .specify ]]; then
    specify init \
      --here \
      --force \
      --non-interactive \
      --ignore-agent-tools \
      --script ps \
      --integration "$ACTIVE_INTEGRATION"
  fi

  local current
  current="$(active_integration || true)"
  if [[ "$current" != "$ACTIVE_INTEGRATION" ]]; then
    specify integration switch "$ACTIVE_INTEGRATION" --script ps
  fi
}

materialize_boundary_skills() {
  uv run --no-project python "$SOURCE_ROOT/$CODEX_SKILL_ADAPTER" \
    --source-root "$SOURCE_ROOT" \
    --project-root .
}

materialize_boundary_runtime() {
  rm -rf "$BOUNDARY_RUNTIME_DIR"
  mkdir -p "$BOUNDARY_RUNTIME_DIR"
  cp -R "$SOURCE_ROOT/src/boundary" "$BOUNDARY_RUNTIME_DIR/boundary"
}

install_adapter() {
  ensure_codex_project

  specify extension add \
    "$SOURCE_ROOT/integration/specdd" \
    --dev \
    --force

  if [[ -d ".specify/presets/${PRESET_ID}" ]]; then
    specify preset remove "$PRESET_ID"
  fi
  specify preset add \
    --dev "$SOURCE_ROOT/integration/specdd-preset" \
    --priority 10

  specify workflow overlay remove \
    "$WORKFLOW_ID" \
    "$WORKFLOW_OVERLAY_ID" >/dev/null 2>&1 || true
  specify workflow overlay add \
    "$SOURCE_ROOT/integration/specdd/workflow-overlay.yml" \
    --priority "$WORKFLOW_OVERLAY_PRIORITY"

  materialize_boundary_runtime
  materialize_boundary_skills
  printf 'Installed Boundary adapter source: %s\n' "$SOURCE"
}

remove_boundary_skills() {
  local skill
  for skill in boundary-scope boundary-implement boundary-contracts; do
    rm -rf ".agents/skills/${skill}"
  done
}

remove_adapter() {
  require_command specify

  if [[ ! -d .specify ]]; then
    printf '%s\n' "Spec Kit is not initialized; nothing to remove."
    remove_boundary_skills
    return
  fi

  specify workflow overlay remove \
    "$WORKFLOW_ID" \
    "$WORKFLOW_OVERLAY_ID" >/dev/null 2>&1 || true

  if [[ -d ".specify/presets/${PRESET_ID}" ]]; then
    specify preset remove "$PRESET_ID"
  fi

  if [[ -d ".specify/extensions/${EXTENSION_ID}" ]]; then
    specify extension remove "$EXTENSION_ID" --force
  fi

  rm -rf "$BOUNDARY_RUNTIME_DIR"
  remove_boundary_skills
}

check_adapter() {
  check_install_prerequisites

  [[ "$(active_integration || true)" == "$ACTIVE_INTEGRATION" ]] ||
    fail "active Spec Kit integration is not ${ACTIVE_INTEGRATION}"
  [[ -d ".specify/extensions/${EXTENSION_ID}" ]] ||
    fail "Boundary Spec Kit adapter extension is not installed"
  [[ -d ".specify/presets/${PRESET_ID}" ]] ||
    fail "Boundary task preset is not installed"
  [[ -f "$BOUNDARY_RUNTIME_DIR/boundary/__init__.py" ]] ||
    fail "generated Boundary runtime is missing"

  local skill overlay_list resolved step
  for skill in \
    speckit-boundary-authorize \
    speckit-boundary-verify \
    boundary-scope \
    boundary-implement \
    boundary-contracts
  do
    [[ -f ".agents/skills/${skill}/SKILL.md" ]] ||
      fail "expected Codex skill is missing: ${skill}"
  done

  overlay_list="$(specify workflow overlay list "$WORKFLOW_ID")"
  grep -Fq "$WORKFLOW_OVERLAY_ID" <<<"$overlay_list" ||
    fail "workflow overlay is not installed"

  resolved="$(specify workflow resolve "$WORKFLOW_ID")"
  for step in boundary-authorize boundary-verify; do
    grep -Fq "$step" <<<"$resolved" ||
      fail "resolved workflow is missing structural step: ${step}"
  done

  printf '%s\n' "Boundary Spec Kit adapter installation is healthy."
}

cleanup() {
  if [[ -n "$TEMP_ROOT" && -d "$TEMP_ROOT" ]]; then
    rm -rf "$TEMP_ROOT"
  fi
}
trap cleanup EXIT

while (($#)); do
  case "$1" in
    --source)
      (($# >= 2)) || fail "--source requires a value"
      SOURCE="$2"
      shift 2
      ;;
    --check)
      ACTION="check"
      shift
      ;;
    --remove)
      ACTION="remove"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

case "$ACTION" in
  install)
    check_install_prerequisites
    materialize_source "$SOURCE"
    require_source_tree
    install_adapter
    ;;
  check)
    check_adapter
    ;;
  remove)
    remove_adapter
    ;;
esac
