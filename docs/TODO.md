# Implementation TODO

Boundary's target architecture is defined in the focused `docs/spec*.md` documents.

The current development baseline still pins Spec Kit `1.0.10`, Codex, and the temporary typed-target SpecDD provider for migration and compatibility evidence. Those are not target product requirements. Project bootstrap no longer initializes or requires the SpecDD framework bootstrap for normal Boundary operation.

The native path provides deterministic canonical contract discovery, parsing, graph construction, target-context resolution, `boundary contracts check`, transient `boundary inspect <target...>`, fresh implementation/contract-evolution authorization, target effective-context identities, Git authorization baselines, atomic current operation records, verified authorization epochs, exact dirty-state carry-forward provenance, and Git-derived actual-write authorization verification with provider-neutral diagnostics.

Canonical Boundary procedure is deterministically materialized from `skills/*/SKILL.md` into Codex discovery state. A second concrete Claude Code materializer exercises the same canonical procedure without introducing a generalized runtime-provider framework. Materialized skill bytes contain only fixed runtime metadata plus canonical procedure and remain independent of feature or operation state.

The Spec Kit integration is now reduced to a change-system adapter surface. Planning and task work use on-demand Boundary inspection rather than persisted context or validation phases. Structured task `Writes:` metadata is projected into native Boundary authorization at implementation entry, and actual Git writes are verified at implementation exit. The adapter uses Boundary host identities, so its public Spec Kit commands are `speckit.boundary.authorize` and `speckit.boundary.verify`; the workflow overlay owns those two blocking transitions. Legacy SpecDD bridge code remains only as migration evidence pending P9 cleanup.

The current `specdd/speckit-boundary` repository/distribution slug and migration-era source layout remain transitional until release ownership and P9 cleanup are complete. They are not runtime or product identities.

The representative two-domain migration fixture now carries native Auth and Users contracts alongside its legacy `.sdd` evidence. Migration parity coverage compares only ownership semantics Boundary deliberately preserves. Legacy `Can modify`, framework/bootstrap, and authority-domain permission behavior is intentionally not translated into native contracts.

Repository contract conversion is complete. Canonical native contracts under `contracts/` now cover provider-neutral core subdomains, agent procedure and concrete runtime adapters, repository tooling, documentation and focused specifications, tests, and the temporary change-adapter migration source. Nested ownership preserves broader core and documentation constraints additively, while the authorization/verification relationship is represented by a narrowly scoped applicability contract.

Work in the order below unless a newly discovered correctness issue requires reprioritization.

## P9 — Migrate this repository off SpecDD

### P9.3 — Remove legacy provider state

- [ ] Remove runtime reliance on `specdd`.
- [ ] Remove the temporary fork-backed CLI provider.
- [ ] Remove remaining `.specdd/` bootstrap compatibility handling.
- [ ] Remove `.sdd` as canonical Boundary contract source.
- [ ] Remove SpecDD-specific resolver, lint, ownership, permission, and intended-target compatibility code.
- [ ] Remove legacy Change Boundary and SpecDD authorization metadata.
- [ ] Delete obsolete SpecDD compatibility docs/tests after native equivalents pass.

Done when:
  A downstream Boundary project contains no `.specdd/` directory, needs no SpecDD CLI, and receives all persistent system semantics from native Boundary contracts.

## P10 — Define the reproducible downstream Boundary experience

- [ ] Define one committed immutable Boundary source/version lock.
- [ ] Include immutable source revision and archive/content checksum.
- [ ] Keep downstream canonical Boundary state limited to:
  - native project contracts;
  - change-system artifacts;
  - the Boundary lock.
- [ ] Make extension/adapter/skill/generated state recreatable.
- [ ] Provide install, health-check, upgrade, remove/reinstall, and fresh-clone reconstruction.
- [ ] Preserve deliberate upgrades rather than silently following a mutable release.
- [ ] Add clean consumer coverage with no canonical Boundary implementation source.
- [ ] Update ignore rules for generated integration and operation state.
- [ ] Split downstream-user setup cleanly from Boundary developer procedures.

Done when:
  A fresh clone can reconstruct the same Boundary tooling and agent capabilities from the committed lock while carrying only native project contracts as persistent Boundary semantics.

## P11 — Final migration cleanup

- [ ] Remove obsolete Spec Kit × SpecDD product terminology from non-historical documentation.
- [ ] Mark or archive historical v0.1 material.
- [ ] Delete the legacy `change-boundary.md` guide after no supported runtime uses that model.
- [ ] Remove compatibility-only tests/helpers and shrink `files.include` accordingly.
- [ ] Keep all code and documentation files below 250 lines.
- [ ] Run the complete supported bootstrap, native contract, authorization, adapter, packaging, and fresh-clone test matrix.

Done when:
  Current documentation describes one Boundary architecture, legacy providers survive only in explicit history if retained at all, and no downstream workflow depends on Spec Kit or SpecDD as product concepts.
