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

The immutable lock schema, lock-aware install/check/remove/reinstall/upgrade lifecycle, generated source provenance, local generated-state exclusions, and separated downstream/development setup are implemented. Remaining work is end-to-end consumer proof against a real immutable Boundary archive.

- [ ] Add a clean-consumer fixture with a committed real `boundary.lock.json` containing an exact Boundary commit archive and checksum, with no canonical Boundary implementation source.
- [ ] Exercise fresh-clone install, health check, checksum failure, remove/reinstall, deliberate upgrade, and failed-upgrade rollback against that fixture.
- [ ] Assert clean-consumer Git status contains no Boundary-owned generated state after reconstruction; decide explicitly how shared Spec Kit registry files are treated if they remain visible.

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
