archive_kind() {
  case "$1" in
    *.zip) printf '%s\n' "zip" ;;
    *.tar.gz|*.tgz) printf '%s\n' "tar.gz" ;;
    *) return 1 ;;
  esac
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
      -path '*/integration/speckit/extension.yml' \
      -print \
      -quit
  )"

  [[ -n "$marker" ]] ||
    fail "archive does not contain integration/speckit/extension.yml"

  SOURCE_ROOT="${marker%/integration/speckit/extension.yml}"
}

materialize_archive() {
  local archive="$1"

  TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/boundary-install.XXXXXX")" ||
    fail "could not create temporary installation directory"
  mkdir -p "$TEMP_ROOT/extracted"
  extract_archive "$archive" "$TEMP_ROOT/extracted"
  locate_source_root "$TEMP_ROOT/extracted"
}

materialize_source() {
  local source="$1"

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
    fail "remote Boundary source requires boundary.lock.json and scripts/consumer.py"
  fi

  fail "source does not exist: ${source}"
}

require_source_tree() {
  [[ -f "$SOURCE_ROOT/integration/speckit/extension.yml" ]] ||
    fail "Spec Kit adapter extension source is missing"
  [[ -f "$SOURCE_ROOT/integration/speckit-preset/preset.yml" ]] ||
    fail "Spec Kit task preset source is missing"
  [[ -f "$SOURCE_ROOT/integration/speckit/workflow-overlay.yml" ]] ||
    fail "Spec Kit workflow overlay source is missing"
  [[ -f "$SOURCE_ROOT/$CODEX_SKILL_ADAPTER" ]] ||
    fail "Codex Boundary skill adapter is missing"
  [[ -f "$SOURCE_ROOT/src/boundary/__init__.py" ]] ||
    fail "native Boundary runtime source is missing"

  local skill
  for skill in scope implement contracts; do
    [[ -f "$SOURCE_ROOT/skills/${skill}/SKILL.md" ]] ||
      fail "canonical Boundary skill is missing: skills/${skill}/SKILL.md"
  done
}
