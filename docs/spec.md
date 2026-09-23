# Spec Kit × SpecDD Integration Specification

Status: v0.1 baseline implemented; provider-neutral public identity migration planned in P4  
Project type: Spec Kit extension/preset integration

## Purpose

This project integrates Spec Kit's feature-oriented development lifecycle with SpecDD's persistent hierarchical system specification model without forking, merging, or duplicating either system.

The core relationship is:

> Spec Kit specifies and coordinates a change. SpecDD specifies the system within which that change occurs and the durable system state the change may produce.

Spec Kit remains responsible for feature specification, clarification, planning, task generation, implementation, analysis, and convergence.

SpecDD remains responsible for persistent structure, ownership, modification authority, dependencies, local system contracts, and durable architectural constraints.

The Spec Kit constitution remains responsible for development governance such as required testing, review, migration, compatibility, and security process.

The current implementation still exposes SpecDD-centered extension, command, workflow, generated-state, and metadata names. P4 in [TODO.md](TODO.md) owns the migration to the provider-neutral `Spec Kit Boundary` / `boundary` public identity. Until that migration lands, operational documentation must describe the names actually implemented rather than mixing planned and current command surfaces.

## Goals

The integration must:

- make applicable SpecDD context available during Spec Kit planning;
- validate plans and tasks against current SpecDD boundaries;
- encourage implementation work to align with SpecDD authority domains;
- distinguish implementation under existing contracts from deliberate contract evolution;
- verify implementation against both feature intent and system intent;
- preserve SpecDD authority semantics;
- keep bridge state derived and reconstructible;
- avoid synchronization between equivalent-looking artifacts;
- remain installable through supported Spec Kit extension mechanisms;
- use the existing SpecDD CLI and resolver rather than reimplementing SpecDD semantics.

The provider-neutral direction does not change those semantic responsibilities. It changes which concepts belong to the product surface and which remain details of the current persistent-contract provider.

## Non-goals

The integration does not:

- replace Spec Kit's task system;
- replace or merge the SpecDD specification format;
- synchronize Spec Kit tasks with SpecDD `Tasks:`;
- maintain duplicated persistent SpecDD constraints in feature artifacts;
- automatically loosen ownership or modification authority;
- silently modify `.sdd` files;
- automatically approve durable architectural changes;
- require a Spec Kit or SpecDD fork;
- provide a general-purpose proof system or GUI;
- introduce a generalized provider-plugin framework merely to hide the current SpecDD dependency.

## Conceptual model

The integration separates four kinds of intent.

### Feature intent

Spec Kit feature artifacts describe the behavior the product or system should exhibit.

Typical artifacts are `spec.md`, user stories, acceptance criteria, and success criteria.

### Implementation intent

Spec Kit planning artifacts describe how the current feature is intended to be implemented.

Typical artifacts are `plan.md`, `tasks.md`, sequencing, and feature-specific technical decisions.

### System intent

The current provider, SpecDD, describes the persistent system model future work must preserve.

Typical artifacts are the `.sdd` hierarchy, inherited constraints, ownership, modification permission, dependencies, references, and component-local contracts.

The durable product concepts are persistent contracts, ownership, modification permission, effective constraints, operation scope, authorization evidence, contract evolution, and implementation verification. P4 separates those concepts from provider-specific invocation and naming without changing the authority semantics already proven by v0.1.

### Development governance

The Spec Kit constitution describes how changes must be developed, reviewed, tested, migrated, or secured.

System architecture belongs in persistent system contracts rather than being duplicated into development-governance policy.

## Authority model

SpecDD is currently authoritative for persistent system boundaries and contracts.

A feature may propose persistent-contract evolution, but a plan or task cannot silently override current authority state. Conflicts are classified rather than resolved by weakening authority.

The bridge recognizes these architectural outcomes:

- `COMPATIBLE`: proposed work fits current contracts and authority.
- `IMPLEMENTATION_CONFLICT`: the feature can remain unchanged, but the proposed implementation violates current constraints.
- `SPEC_EVOLUTION_REQUIRED`: the requested behavior requires a durable system-contract change.
- `AUTHORITY_EVOLUTION_REQUIRED`: the requested behavior requires persistent ownership or modification-permission change.

A multi-domain feature is not by itself evidence that specification or authority evolution is required.

These classifications describe bridge semantics. Their current SpecDD-specific transport and naming are implementation details that P4 may rename or isolate without weakening the behavior.

## Authority snapshot invariant

An implementation operation cannot grant itself authority by changing its governing persistent contract and immediately relying on the new rule.

With the current SpecDD provider, the supported sequence is:

1. identify the required specification or authority change;
2. apply that `.sdd` evolution separately;
3. end the previous authority context when authority changed;
4. refresh the feature Change Boundary and effective SpecDD context;
5. authorize a new implementation operation;
6. begin dependent implementation under the new evidence.

This invariant applies especially to ownership changes, `Can modify` changes, cross-domain write permission, and other write-scope expansion.

The invariant belongs to the bridge architecture rather than to the SpecDD product name. A future provider replacement must preserve equivalent operation separation unless the architecture is deliberately redesigned.

## Focused design documents

The remaining design is split by responsibility:

- [spec-architecture.md](spec-architecture.md) defines the Change Boundary, task semantics, bridge layers, and deterministic adapter responsibilities.
- [spec-lifecycle.md](spec-lifecycle.md) defines lifecycle commands, specification evolution, convergence, promotion, and governance separation.
- [spec-v0.1.md](spec-v0.1.md) records the historical v0.1 scope, fixture scenarios, acceptance criteria, and design principles that established the current baseline.
- [change-boundary.md](change-boundary.md) provides the detailed operational model for boundary refresh, context fingerprints, authorization evidence, and verification baselines.
- [development.md](development.md) owns development-host setup, packaging mechanics, rematerialization, and maintenance procedures.
- [TODO.md](TODO.md) owns active migration and downstream-user work rather than completed implementation history.

Command-specific procedures remain in the canonical bridge command contracts under `integration/specdd/commands/` until the P4 source/identity migration replaces that path.

## Documentation boundaries

Documentation should explain one implemented source of truth for each concern:

- feature and implementation intent: Spec Kit artifacts;
- persistent system semantics: the active persistent-contract provider;
- development governance: the Spec Kit constitution;
- refreshable operation context: Change Boundary and context identity;
- historical implementation authority: authorization evidence;
- implementation procedures: command and workflow contracts;
- development and packaging procedures: `development.md`;
- active future work: `TODO.md`.

Historical acceptance material should remain identifiable as historical rather than silently becoming the current architecture contract.

## Summary invariant

The integration is correctly designed while this remains true:

> Spec Kit owns the change model. The persistent-contract provider owns the durable system model. The bridge projects the latter onto the former without merging or duplicating either.

The current provider is SpecDD. P4 changes the public bridge identity so replacing or upgrading that provider does not require renaming the product-level architecture.
