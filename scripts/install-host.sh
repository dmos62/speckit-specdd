active_integration() {
  [[ -f .specify/integration.json ]] || return 1
  uv run --no-project python - .specify/integration.json <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
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
    "$SOURCE_ROOT/integration/speckit" \
    --dev \
    --force

  if [[ -d ".specify/presets/${PRESET_ID}" ]]; then
    specify preset remove "$PRESET_ID"
  fi
  specify preset add \
    --dev "$SOURCE_ROOT/integration/speckit-preset" \
    --priority 10

  specify workflow overlay remove \
    "$WORKFLOW_ID" \
    "$WORKFLOW_OVERLAY_ID" >/dev/null 2>&1 || true
  specify workflow overlay add \
    "$SOURCE_ROOT/integration/speckit/workflow-overlay.yml" \
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
