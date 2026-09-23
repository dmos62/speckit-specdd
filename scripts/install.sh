#!/usr/bin/env bash
set -euo pipefail

readonly SPECKIT_VERSION="1.0.10"
readonly ACTIVE_INTEGRATION="codex"
readonly EXTENSION_ID="specdd"
readonly PRESET_ID="specdd-bridge"
readonly WORKFLOW_ID="speckit"
readonly WORKFLOW_OVERLAY_ID="specdd-bridge"
readonly WORKFLOW_OVERLAY_PRIORITY="10"

ACTION="install"
SOURCE="."
TEMP_ROOT=""
SOURCE_ROOT=""

fail() {
  printf 'install: %s\n' "$*" >&2
  exit 1
}

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

specdd_supports_intended_targets() {
  local help flag
  help="$(specdd resolve --help 2>&1)" || return 1
  for flag in --file --folder --sdd-file; do
    grep -Fq -- "$flag" <<<"$help" || return 1
  done
}

check_install_prerequisites() {
  require_command specify
  require_command uv
  require_command specdd
  require_command codex
  speckit_matches_pin ||
    fail "Spec Kit ${SPECKIT_VERSION} is required"
  specdd_supports_intended_targets ||
    fail "SpecDD resolver must support --file, --folder, and --sdd-file"
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

archive_kind() {
  local value="${1%%\?*}"
  case "$value" in
    *.zip) printf '%s\n' "zip" ;;
    *.tar.gz|*.tgz) printf '%s\n' "tar.gz" ;;
    *) return 1 ;;
  esac
}

immutable_github_archive() {
  local value="${1%%\?*}"

  case "$value" in
    https://github.com/*/*/archive/refs/tags/*.zip|\
    https://github.com/*/*/archive/refs/tags/*.tar.gz|\
    https://github.com/*/*/archive/refs/tags/*.tgz|\
    https://github.com/*/*/releases/download/*/*.zip|\
    https://github.com/*/*/releases/download/*/*.tar.gz|\
    https://github.com/*/*/releases/download/*/*.tgz)
      return 0
      ;;
  esac

  [[ "$value" =~ ^https://github\.com/[^/]+/[^/]+/archive/[0-9a-fA-F]{40}\.(zip|tar\.gz|tgz)$ ]]
}

extract_archive() {
  local archive="$1"
  local destination="$2"

  uv run --no-project python - "$archive" "$destination" <<'PY'
import shutil
import sys

shutil.unpack_archive(sys.argv[1], sys.argv[2])
PY
}

locate_source_root() {
  local extracted="$1"
  local marker

  marker="$(
    find "$extracted" \
      -type f \
      -path '*/integration/specdd/extension.yml' \
      -print \
      -quit
  )"

  [[ -n "$marker" ]] ||
    fail "archive does not contain integration/specdd/extension.yml"

  SOURCE_ROOT="${marker%/integration/specdd/extension.yml}"
}

materialize_archive() {
  local archive="$1"

  TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/speckit-boundary-install.XXXXXX")" ||
    fail "could not create temporary installation directory"
  mkdir -p "$TEMP_ROOT/extracted"
  extract_archive "$archive" "$TEMP_ROOT/extracted"
  locate_source_root "$TEMP_ROOT/extracted"
}

materialize_source() {
  local source="$1"
  local kind archive

  if [[ -d "$source" ]]; then
    SOURCE_ROOT="$(cd "$source" && pwd -P)"
    return
  fi

  if [[ -f "$source" ]]; then
    archive_kind "$source" >/dev/null ||
      fail "local source must be a directory, .zip, .tar.gz, or .tgz archive"
    materialize_archive "$source"
    return
  fi

  if [[ "$source" == http://* || "$source" == https://* ]]; then
    immutable_github_archive "$source" ||
      fail "remote source must be an immutable GitHub tag, commit, or release archive URL"
    kind="$(archive_kind "$source")" ||
      fail "remote archive must be .zip, .tar.gz, or .tgz"
    require_command curl
    TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/speckit-boundary-install.XXXXXX")" ||
      fail "could not create temporary installation directory"
    archive="$TEMP_ROOT/source.${kind}"
    curl \
      -fsSL \
      --proto '=https' \
      --tlsv1.2 \
      --max-redirs 5 \
      -o "$archive" \
      "$source"
    mkdir -p "$TEMP_ROOT/extracted"
    extract_archive "$archive" "$TEMP_ROOT/extracted"
    locate_source_root "$TEMP_ROOT/extracted"
    return
  fi

  fail "source does not exist: ${source}"
}

require_source_tree() {
  [[ -f "$SOURCE_ROOT/integration/specdd/extension.yml" ]] ||
    fail "extension source is missing"
  [[ -f "$SOURCE_ROOT/integration/specdd-preset/preset.yml" ]] ||
    fail "preset source is missing"
  [[ -f "$SOURCE_ROOT/integration/specdd/workflow-overlay.yml" ]] ||
    fail "workflow overlay source is missing"
}

install_bridge() {
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

  printf 'Installed bridge source: %s\n' "$SOURCE"
}

remove_bridge() {
  require_command specify

  if [[ ! -d .specify ]]; then
    printf '%s\n' "Spec Kit is not initialized; nothing to remove."
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
}

check_bridge() {
  check_install_prerequisites

  [[ "$(active_integration || true)" == "$ACTIVE_INTEGRATION" ]] ||
    fail "active Spec Kit integration is not ${ACTIVE_INTEGRATION}"
  [[ -d ".specify/extensions/${EXTENSION_ID}" ]] ||
    fail "bridge extension is not installed"
  [[ -d ".specify/presets/${PRESET_ID}" ]] ||
    fail "bridge preset is not installed"

  local skill overlay_list resolved step
  for skill in \
    speckit-specdd-context \
    speckit-specdd-validate \
    speckit-specdd-authorize \
    speckit-specdd-verify
  do
    [[ -f ".agents/skills/${skill}/SKILL.md" ]] ||
      fail "expected Codex skill is missing: ${skill}"
  done

  overlay_list="$(specify workflow overlay list "$WORKFLOW_ID")"
  grep -Fq "$WORKFLOW_OVERLAY_ID" <<<"$overlay_list" ||
    fail "workflow overlay is not installed"

  resolved="$(specify workflow resolve "$WORKFLOW_ID")"
  for step in \
    specdd-context \
    specdd-task-validation \
    specdd-authorize \
    specdd-verify
  do
    grep -Fq "$step" <<<"$resolved" ||
      fail "resolved workflow is missing structural step: ${step}"
  done

  printf '%s\n' "Spec Kit bridge installation is healthy."
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
    install_bridge
    ;;
  check)
    check_bridge
    ;;
  remove)
    remove_bridge
    ;;
esac
