# Implementation TODO

Boundary's target architecture is defined in the focused `docs/spec*.md` documents.

The current executable baseline still uses Spec Kit `1.0.10`, Codex, and the temporary typed-target SpecDD provider. Those are migration dependencies, not target product requirements. Project bootstrap no longer initializes or requires the SpecDD framework bootstrap for normal Boundary operation.

The native path now provides deterministic canonical contract discovery, parsing, graph construction, target-context resolution, `boundary contracts check`, transient `boundary inspect <target...>`, fresh implementation/contract-evolution authorization, target effective-context identities, Git authorization baselines, atomic current operation records, verified authorization epochs, exact dirty-state carry-forward provenance, and Git-derived actual-write authorization verification with provider-neutral diagnostics.

Canonical Boundary procedure is now deterministically materialized from `skills/*/SKILL.md` into Codex discovery state. A second concrete Claude Code materializer exercises the same canonical procedure without introducing a generalized runtime-provider framework. Materialized skill bytes contain only fixed runtime metadata plus canonical procedure and remain independent of feature or operation state.

Work in the order below unless a newly discovered correctness issue requires reprioritization.

## P8 — Reduce Spec Kit to a change-system adapter

The provider-neutral change-system adapter contract is defined in `docs/spec-change-adapter.md`.

### P8.2 — Simplify Spec Kit integration

- [ ] Replace current public SpecDD command identity with Boundary adapter commands where still needed.
- [ ] Make the product CLI `boundary ...`; treat `speckit.boundary.*` only as adapter wrappers.
- [ ] Remove the public `context` lifecycle state.
- [ ] Remove the public `validate` lifecycle state.
- [ ] Use on-demand inspection during plan/task work.
- [ ] Keep deterministic structural enforcement only around authorization and verification.
- [ ] Remove duplicated extension hooks when the workflow overlay already enforces the same transition.
- [ ] Reduce the preset to tiny skill/write-metadata integration or remove it entirely if supported skill discovery makes it unnecessary.

### P8.3 — Remove Spec Kit from product naming

- [ ] Use `Boundary` as the display/product identity.
- [ ] Use `boundary` for extension/runtime/CLI identities where the host permits it.
- [ ] Keep Spec Kit naming only in the Spec Kit adapter.
- [ ] Treat the current repository/distribution slug as transitional until release ownership is finalized.
- [ ] Add stale-public-identity tests after the migration is atomic enough to avoid false positives.

Done when:
  Replacing Spec Kit requires a new change adapter rather than changes to native contracts, authorization, skills, or verification.

## P9 — Migrate this repository off SpecDD

### P9.1 — Introduce native contracts alongside legacy fixtures

- [ ] Translate representative existing `.sdd` ownership and durable semantics into native contracts.
- [ ] Add parity tests only for semantics Boundary deliberately preserves.
- [ ] Do not preserve SpecDD behavior merely because it exists.
- [ ] Use the temporary SpecDD adapter only as migration evidence.

### P9.2 — Convert repository contracts

- [ ] Create native contracts for current Boundary source, adapters, scripts, docs, and tests.
- [ ] Preserve useful hierarchical constraints through nested ownership plus additive applicability.
- [ ] Replace broad cross-contract prose with narrowly scoped relationship contracts only where the relationship is durable and useful.
- [ ] Avoid a repository-wide catch-all contract.

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
