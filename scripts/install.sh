#!/usr/bin/env bash
set -euo pipefail

readonly SPECKIT_VERSION="1.0.10"
readonly SPECKIT_TAG="v${SPECKIT_VERSION}"
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

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 ||
    fail "required command not found: ${command_name}"
}

speckit_matches_pin() {
  command -v specify >/dev/null 2>&1 &&
    specify --version 2>&1 |
      grep -Eq "(^|[^0-9])${SPECKIT_VERSION//./\\.}([^0-9]|$)"
}

ensure_install_prerequisites() {
  require_command git
  require_command uv
  require_command codex

  if ! speckit_matches_pin; then
    uv tool install specify-cli --force \
      --from "git+https://github.com/github/spec-kit.git@${SPECKIT_TAG}"
  fi
  speckit_matches_pin ||
    fail "Spec Kit ${SPECKIT_VERSION} could not be installed"
}

check_install_prerequisites() {
  require_command git
  require_command uv
  require_command codex
  require_command specify
  speckit_matches_pin ||
    fail "Spec Kit ${SPECKIT_VERSION} is required"
}

source "$INSTALL_SCRIPT_DIR/install-source.sh"
source "$INSTALL_SCRIPT_DIR/install-host.sh"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install.sh [--source <directory|archive>]
  bash scripts/install.sh --check
  bash scripts/install.sh --remove

This script installs from already materialized Boundary source and is intended
for Boundary development and the locked downstream consumer.

Downstream repositories should use boundary.lock.json with scripts/consumer.py.
Direct mutable or unchecked remote source installation is not supported here.
EOF
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
    ensure_install_prerequisites
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
