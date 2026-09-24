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

install_specdd_compat_provider() {
  local checkout package_archive source_version
  checkout="$(mktemp -d "${TMPDIR:-/tmp}/specdd-cli.XXXXXX")" ||
    fail "could not create a temporary SpecDD CLI checkout"

  if ! git clone \
    --depth 1 \
    --branch "$SPECDD_COMPAT_CLI_REF" \
    "$SPECDD_COMPAT_CLI_REPOSITORY" \
    "$checkout"
  then
    rm -rf "$checkout"
    fail "could not clone temporary SpecDD resolver provider ${SPECDD_COMPAT_CLI_REPOSITORY}#${SPECDD_COMPAT_CLI_REF}"
  fi

  source_version="$(
    node -e \
      'const p=require(process.argv[1]);process.stdout.write(p.version)' \
      "$checkout/package.json"
  )"
  if [[ "$source_version" != "$SPECDD_COMPAT_CLI_VERSION" ]]; then
    rm -rf "$checkout"
    fail "temporary SpecDD resolver provider reports ${source_version:-unknown}; expected ${SPECDD_COMPAT_CLI_VERSION}"
  fi

  if ! (
    cd "$checkout" &&
      npm ci &&
      npm run build &&
      npm pack --silent > .specdd-package
  ); then
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
