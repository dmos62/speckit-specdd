# Implementation TODO

Boundary's target architecture is defined in the focused `docs/spec*.md` documents.

The current integration baseline still pins Spec Kit `1.0.10` and Codex for development and compatibility coverage. Those are integration choices rather than target product requirements.

Boundary no longer installs, invokes, or requires SpecDD for normal operation. Native contracts under `contracts/` are the only persistent Boundary contract source. Authorization and verification use fresh native contract state, exact structured writes, Git baselines, atomic operation records, verified authorization epochs, and exact dirty-state carry-forward provenance.

Canonical Boundary procedure is deterministically materialized from `skills/*/SKILL.md` into Codex discovery state. A second concrete Claude Code materializer exercises the same canonical procedure without introducing a generalized runtime-provider framework. Materialized skill bytes contain only fixed runtime metadata plus canonical procedure and remain independent of feature or operation state.

The Spec Kit integration is a change-system adapter only. Planning and task work use on-demand Boundary inspection rather than persisted context or validation phases. Structured task `Writes:` metadata is projected into native Boundary authorization at implementation entry, and actual Git writes are verified at implementation exit. The adapter uses Boundary host identities, so its public Spec Kit commands are `speckit.boundary.authorize` and `speckit.boundary.verify`; the workflow overlay owns those two blocking transitions.

Repository contract conversion is complete. Canonical native contracts under `contracts/` cover provider-neutral core subdomains, agent procedure and concrete runtime adapters, repository tooling, documentation and focused specifications, tests, and the concrete Spec Kit change adapter. Nested ownership preserves broader core and documentation constraints additively, while the authorization/verification relationship is represented by a narrowly scoped applicability contract.

Historical migration fixtures and v0.1 documentation may still describe SpecDD behavior, but they are not runtime inputs. Final terminology, historical-material, and compatibility-test cleanup remains P11 work.

Work in the order below unless a newly discovered correctness issue requires reprioritization.

## P10 — Define the reproducible downstream Boundary experience

The immutable lock schema, lock-aware install/check/remove/reinstall/upgrade lifecycle, generated source provenance, local generated-state exclusions, and separated downstream/development setup are implemented.

Checksum-verified archive lifecycle coverage now exercises a fresh cloned consumer repository through install, health check, checksum failure, remove/reinstall, deliberate upgrade, and failed-upgrade rollback without placing canonical Boundary implementation source in the consumer. It also verifies that Boundary-owned generated paths stay out of Git status while shared host registry changes remain visible and reviewable.

Release fixture initialization excludes the harness-only `boundary-upgrade.lock.json` from the simulated downstream repository, so the clean consumer carries only its active `boundary.lock.json`. Release coverage also requires the initial and upgrade locks to name distinct immutable revisions.

This local archive coverage does not replace the remaining release proof against a published immutable Boundary commit archive.

- [ ] Add a clean-consumer fixture with a committed real `boundary.lock.json` containing an exact Boundary commit archive and checksum, with no canonical Boundary implementation source.
- [ ] Run the same fresh-clone lifecycle matrix against that committed real archive fixture.

Release-proof harness coverage is prepared in `tests/test_consumer_release.py`. It is opt-in with `BOUNDARY_RELEASE_ARCHIVE_TESTS=1`, and `dev-scripts.include` runs it automatically once both release lock fixtures exist. Completion still requires real published archive evidence: commit `tests/fixtures/consumer-release/boundary.lock.json` and `boundary-upgrade.lock.json` with distinct immutable Boundary sources and exact SHA-256 values. Do not substitute synthetic archive bytes for this proof.

The repository publication identity is now known as `https://github.com/dmos62/speckit-specdd.git`. At the latest captured check, published remote HEAD was `a016187ce6107d7b1abc1e108669d463a104cb82`, while local HEAD was `6d3a0c658c5c2c7097b95e1571c7f5abea8318fd` and was not contained by a remote branch. Two published commits containing the current release-proof implementation are therefore not yet established.

`dev-scripts.include` now fetches published refs, searches remote history for the newest two commits containing the complete downstream consumer and release-proof source, and attempts an anonymous download of each exact GitHub commit archive to calculate its SHA-256. Treat a candidate as usable only when both revisions are published and both archive checksums are successfully reported. The older candidate is the initial fixture and the newer candidate is the upgrade fixture.

The publication step that cannot be manufactured by repository code is tracked in `HUMAN-REQUEST.md`. Once suitable commits are published and the candidate report provides two exact revisions, URLs, and checksums, add the two real lock fixtures, run the release lifecycle test, remove the human request, and complete P10.

Done when:
  A fresh clone can reconstruct the same Boundary tooling and agent capabilities from the committed lock while carrying only native project contracts as persistent Boundary semantics.

## P11 — Final migration cleanup

- [ ] Remove obsolete Spec Kit × SpecDD product terminology from non-historical documentation.
- [ ] Mark or archive historical v0.1 material.
- [ ] Delete the legacy `change-boundary.md` guide after no supported runtime uses that model.
- [ ] Remove compatibility-only tests/helpers and shrink `files.include` accordingly. The obsolete native-contract migration test that imported the removed SpecDD adapter has been deleted; audit remaining compatibility helpers before completing this item.
- [ ] Keep all code and documentation files below 250 lines.
- [ ] Run the complete supported bootstrap, native contract, authorization, adapter, packaging, and fresh-clone test matrix.

Done when:
  Current documentation describes one Boundary architecture, legacy providers survive only in explicit history if retained at all, and no downstream workflow depends on Spec Kit or SpecDD as product concepts.
