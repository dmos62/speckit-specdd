# Spec Kit × SpecDD Integration Specification

Status: Draft  
Target release: v0.1  
Project type: Spec Kit extension/preset integration  
Primary goal: Integrate SpecDD's persistent hierarchical system specification model into Spec Kit's feature-oriented specification and implementation workflow without forking or duplicating either system.

## 1. Purpose

This project unifies complementary aspects of Spec Kit and SpecDD.

Spec Kit remains responsible for the lifecycle of a change:

- feature specification,
- clarification,
- planning,
- task generation,
- implementation,
- analysis,
- convergence.

SpecDD remains responsible for the persistent structural model of the system:

- hierarchical specifications,
- inherited constraints,
- ownership,
- read/write boundaries,
- dependencies,
- local system contracts,
- durable architectural invariants.

The integration provides the semantic bridge between these models.

The core relationship is:

> Spec Kit specifies and coordinates a change. SpecDD specifies the system within which that change occurs and the durable system state the change may produce.

The project MUST use Spec Kit's extension mechanisms rather than modify or fork Spec Kit core.

The project SHOULD use SpecDD's existing CLI and resolver rather than reimplement SpecDD semantics.

---

## 2. Goals

The integration MUST:

1. Make applicable SpecDD context available during Spec Kit planning.
2. Validate Spec Kit plans and tasks against SpecDD boundaries.
3. Encourage implementation tasks to align with SpecDD authority domains.
4. Distinguish implementation under existing system contracts from deliberate evolution of those contracts.
5. Verify the resulting implementation against both:
   - Spec Kit feature intent, and
   - SpecDD system intent.
6. Preserve SpecDD's authority semantics.
7. Keep derived integration state reconstructible rather than creating another source of truth.
8. Avoid synchronization between equivalent-looking artifacts where synchronization would create duplication.
9. Remain installable as an independent Spec Kit integration.
10. Avoid requiring modifications to Spec Kit or SpecDD upstream code.

---

## 3. Non-goals

v0.1 MUST NOT attempt to:

- replace Spec Kit's task system,
- replace SpecDD's specification format,
- merge Spec Kit and SpecDD file formats,
- reimplement the SpecDD parser or resolver,
- maintain duplicated copies of SpecDD constraints inside Spec Kit artifacts,
- synchronize Spec Kit tasks with SpecDD `Tasks:` entries,
- automatically loosen SpecDD authority,
- silently modify `.sdd` files,
- automatically approve durable architectural changes,
- create a general-purpose formal proof system for specifications,
- solve every possible cross-boundary architectural conflict,
- provide a GUI,
- require a custom Spec Kit fork.

---

## 4. Conceptual model

The integration recognizes four distinct categories of intent.

### 4.1 Feature intent

Owned by Spec Kit.

Typical artifacts:

- `spec.md`
- feature acceptance criteria
- user stories
- success criteria

Feature intent answers:

> What change should the product or system exhibit?

### 4.2 Implementation intent

Owned by Spec Kit.

Typical artifacts:

- `plan.md`
- `tasks.md`
- implementation sequencing
- technical decisions specific to the feature

Implementation intent answers:

> How is this change currently intended to be implemented?

### 4.3 System intent

Owned by SpecDD.

Typical artifacts:

- `.sdd` hierarchy
- inherited `Must` and `Must not` rules
- `Owns`
- `Can modify`
- `Can read`
- `Depends on`
- references
- component-local contracts

System intent answers:

> What is this part of the system, and what constraints govern it?

### 4.4 Development governance

Owned by the Spec Kit constitution.

Typical concerns:

- required testing practices,
- review requirements,
- migration policies,
- security process,
- compatibility requirements,
- engineering process rules.

Development governance answers:

> How must changes to this project be developed?

---

## 5. Authority model

The integration MUST treat SpecDD as authoritative for persistent system boundaries and contracts.

A Spec Kit feature MAY propose changing SpecDD.

A Spec Kit plan or task MUST NOT silently override SpecDD.

A detected conflict MUST be classified rather than automatically resolved by relaxing constraints.

At minimum, the integration MUST support these classifications:

- `COMPATIBLE`
- `IMPLEMENTATION_CONFLICT`
- `SPEC_EVOLUTION_REQUIRED`
- `AUTHORITY_EVOLUTION_REQUIRED`

### 5.1 COMPATIBLE

The proposed work fits the current SpecDD contracts and authority model.

### 5.2 IMPLEMENTATION_CONFLICT

The desired feature does not inherently require system-contract evolution, but the proposed implementation violates an existing SpecDD rule.

Expected response:

- preserve the feature,
- revise the implementation.

### 5.3 SPEC_EVOLUTION_REQUIRED

The requested behavior requires a durable change to the system contract.

Expected response:

- make the required SpecDD evolution explicit,
- separate it from ordinary implementation work,
- apply it deliberately,
- re-resolve SpecDD context before implementation continues.

### 5.4 AUTHORITY_EVOLUTION_REQUIRED

The requested behavior requires a change to ownership, write authority, or another authority boundary.

Expected response:

- surface the authority change explicitly,
- do not treat the current operation as authorized by the newly proposed rule,
- apply the authority change separately,
- begin a new resolution/implementation operation after the new authority state exists.

---

## 6. Authority snapshot invariant

The integration MUST preserve the following invariant:

> A task or implementation operation MUST NOT grant itself new authority by modifying the SpecDD specification that governs that same operation and then immediately relying on that new authority.

The supported sequence is:

1. detect required SpecDD evolution,
2. propose the `.sdd` delta,
3. deliberately apply the specification change,
4. end the current authority context,
5. re-resolve applicable SpecDD state,
6. begin implementation under the newly resolved authority.

This rule applies especially to:

- ownership changes,
- `Can modify` changes,
- new cross-domain write permissions,
- changes that materially expand the operation's write scope.

---

## 7. Change Boundary

The central integration abstraction is the `ChangeBoundary`.

A Change Boundary is a derived projection of the persistent SpecDD system model onto one Spec Kit feature.

It answers:

> Which portions of the SpecDD-governed system does this feature inhabit?

The Change Boundary MUST be:

- derived,
- reproducible,
- safe to delete,
- regenerated from source artifacts,
- treated as cache/integration state rather than authoritative specification.

### 7.1 Initial storage location

For a feature such as:

`specs/001-google-login/`

the derived state SHOULD be stored under:

`specs/001-google-login/.specdd/boundary.json`

### 7.2 Required Change Boundary fields

The initial schema SHOULD contain:

- schema version,
- feature identifier,
- resolved targets,
- governing specifications,
- primary authority per target where determinable,
- distinct authority domains involved,
- whether the feature crosses authority domains,
- unresolved targets or ambiguities,
- generation metadata sufficient for diagnostics.

Example:

{
  "schemaVersion": 1,
  "feature": "001-google-login",
  "targets": [
    {
      "path": "src/auth/google.ts",
      "primaryAuthority": "src/auth/auth.sdd",
      "resolvedSpecs": [
        "project.sdd",
        "src/auth/auth.sdd"
      ]
    },
    {
      "path": "src/users/identity.ts",
      "primaryAuthority": "src/users/users.sdd",
      "resolvedSpecs": [
        "project.sdd",
        "src/users/users.sdd"
      ]
    }
  ],
  "authorities": [
    "src/auth/auth.sdd",
    "src/users/users.sdd"
  ],
  "crossBoundary": true,
  "unresolved": []
}

### 7.3 Derived-data rule

The Change Boundary MUST NOT become a second copy of SpecDD.

In particular, it SHOULD NOT duplicate the full text of:

- `Must`,
- `Must not`,
- ownership rules,
- dependency declarations,
- other persistent constraints,

unless required transiently for one execution.

The canonical source remains the `.sdd` hierarchy.

---

## 8. Target discovery

The integration needs a set of system targets before it can resolve SpecDD context.

Target discovery MAY use:

- explicit file paths in `plan.md`,
- explicit file paths in `tasks.md`,
- paths proposed by the planning agent,
- existing implementation paths related to the feature,
- paths supplied directly to the bridge command.

Target discovery is expected to become more precise as the feature progresses.

Therefore, the Change Boundary MAY evolve between:

- planning,
- task generation,
- implementation,
- verification.

The integration SHOULD regenerate or validate the boundary at lifecycle gates rather than assuming an early boundary remains complete.

---

## 9. Task semantics

Spec Kit remains the canonical execution/task system for feature work.

SpecDD `Tasks:` MUST NOT be synchronized with Spec Kit `tasks.md`.

They have different meanings:

- Spec Kit tasks represent feature/change execution.
- SpecDD tasks represent local system/spec planning context.

### 9.1 Primary authority rule

A Spec Kit implementation task SHOULD normally have one primary SpecDD authority for its write set.

This is a heuristic and validation rule, not a requirement that one user story map to one authority.

User stories MAY cross any number of SpecDD domains.

### 9.2 Task partitioning

Given one feature:

`US1: User can sign in with Google`

the integration SHOULD prefer authority-aligned implementation tasks such as:

- Auth: implement Google provider
- Users: associate external identity
- API: expose login endpoint

rather than one task that writes broadly across all three domains.

### 9.3 Cross-boundary tasks

A task that spans multiple authorities MUST NOT automatically be rejected.

The integration SHOULD determine whether the cross-boundary work is:

- naturally decomposable,
- explicitly permitted,
- contract/interface work,
- legitimate system evolution,
- an accidental architectural boundary violation.

The bridge MAY recommend a split.

It MUST NOT automatically change durable system authority merely to make the task valid.

---

## 10. Task classifications

The integration SHOULD classify feature tasks into at least:

### NORMAL

Implementation under current SpecDD contracts.

### CROSS_BOUNDARY

Implementation intentionally involving multiple authority domains or contracts without requiring persistent authority evolution.

### SPEC_EVOLUTION

Work that changes durable system behavior or architectural contracts represented by SpecDD.

### AUTHORITY_EVOLUTION

Work that changes persistent ownership or permission boundaries.

These classifications MAY initially exist only in analysis output.

They MAY later become explicit metadata if doing so proves useful.

---

## 11. Promotion from Spec Kit to SpecDD

Not every feature requirement or implementation decision should become persistent SpecDD specification.

The integration SHOULD use this conceptual promotion test:

> If this information were forgotten after the feature shipped, could a future developer make a locally reasonable but systemically invalid change?

If yes, the information is a candidate for promotion into SpecDD.

Typical candidates for SpecDD promotion:

- durable architectural invariants,
- persistent component contracts,
- ownership rules,
- cross-component interaction contracts,
- security invariants,
- dependency restrictions,
- local behavioral rules that future work must preserve.

Typical information that SHOULD remain only in Spec Kit history:

- one-time migration steps,
- feature-specific rollout tasks,
- temporary implementation sequencing,
- acceptance metrics that are not durable system contracts,
- implementation details that may safely change later,
- historical discussion.

Promotion MUST be deliberate.

v0.1 MUST NOT automatically edit `.sdd` files based on this heuristic.

---

## 12. Constitution versus root SpecDD

The integration MUST avoid turning the Spec Kit constitution and root SpecDD specification into duplicate policy stores.

The intended separation is:

### Spec Kit constitution

Development governance.

Examples:

- every bug fix requires a regression test,
- migrations require rollback procedures,
- public API changes require compatibility checks,
- security-sensitive work requires threat modeling.

### Root SpecDD specification

System/product governance.

Examples:

- domain modules do not depend on transport,
- frontend code cannot access database modules,
- services communicate through defined contracts,
- persistence is isolated behind repository boundaries.

When overlap occurs, the project SHOULD move the rule to the layer that matches its semantic purpose.

---

## 13. Integration architecture

The integration SHOULD consist of four layers.

### 13.1 SpecDD bridge extension

Responsibilities:

- expose bridge commands,
- invoke SpecDD tooling,
- construct derived Change Boundaries,
- perform integration validation,
- expose verification diagnostics,
- participate in Spec Kit lifecycle hooks.

Initial commands:

- `speckit.specdd.context`
- `speckit.specdd.validate`
- `speckit.specdd.verify`

### 13.2 Spec Kit preset

Responsibilities:

- augment planning instructions,
- augment task-generation instructions,
- augment convergence reasoning,
- expose SpecDD context while Spec Kit artifacts are being created rather than only checking afterward.

The preset SHOULD wrap or compose upstream behavior.

It SHOULD NOT copy complete upstream templates where wrapping is sufficient.

### 13.3 Workflow overlay

Responsibilities:

- add deterministic lifecycle gates,
- ensure validation occurs at appropriate transition points,
- avoid relying solely on an agent remembering to run bridge commands.

The workflow overlay SHOULD be introduced after the individual commands work reliably.

### 13.4 Bundle

Responsibilities:

- package the extension,
- package the preset,
- package the workflow overlay,
- pin compatible versions,
- make the integration installable as one coherent unit.

The bundle is a packaging milestone, not part of the first implementation slice.

---

## 14. Bridge commands

### 14.1 `speckit.specdd.context`

Purpose:

Construct or refresh the Change Boundary for the active feature.

Inputs MAY include:

- active feature directory,
- target paths,
- current plan,
- current task list.

Responsibilities:

1. discover candidate target paths,
2. call SpecDD resolution for each relevant target,
3. normalize resolver results,
4. identify governing authority domains,
5. record unresolved or ambiguous paths,
6. write `.specdd/boundary.json`,
7. present actionable context to the calling Spec Kit workflow.

The command MUST use SpecDD's existing resolver wherever possible.

### 14.2 `speckit.specdd.validate`

Purpose:

Validate feature artifacts against current SpecDD context.

Inputs:

- feature specification,
- plan,
- tasks,
- current Change Boundary,
- fresh SpecDD resolution where appropriate.

Initial diagnostics SHOULD include:

- task crosses multiple authority domains,
- target has no resolvable SpecDD context,
- plan writes outside apparent authority,
- plan contradicts a durable SpecDD constraint,
- requested behavior appears to require spec evolution,
- requested behavior appears to require authority evolution,
- Change Boundary is stale or incomplete.

The validator SHOULD distinguish:

- errors,
- warnings,
- informational findings,
- proposed task decomposition.

### 14.3 `speckit.specdd.verify`

Purpose:

Verify the resulting implementation against SpecDD after code changes exist.

Inputs SHOULD include:

- actual changed paths,
- current feature artifacts,
- freshly resolved SpecDD context,
- relevant verification output.

Responsibilities:

- verify actual writes against authority boundaries,
- identify SpecDD drift,
- identify implementation that satisfies the feature but violates system intent,
- identify durable changes that appear to be missing corresponding SpecDD evolution,
- report unresolved ambiguities.

---

## 15. Convergence semantics

The combined convergence model is:

Feature correctness:

- implementation satisfies Spec Kit feature intent.

System correctness:

- resulting system satisfies current SpecDD contracts.

Governance correctness:

- work satisfies the Spec Kit constitution.

The integration SHOULD introduce or recognize diagnostic classes such as:

- `FEATURE_GAP`
- `CONTRADICTS_FEATURE`
- `SPECDD_VIOLATION`
- `SPECDD_DRIFT`
- `MISSING_SPEC_EVOLUTION`
- `AUTHORITY_VIOLATION`
- `CONSTITUTION_VIOLATION`

Authority verification and convergence MUST remain conceptually distinct.

Authority verification asks:

> Was this operation permitted under the governing system boundaries?

Convergence asks:

> Is the resulting implementation consistent with the feature, system, and governance intent?

---

## 16. Deterministic versus agentic responsibilities

The integration SHOULD move objective mechanics into deterministic code and retain ambiguous architectural reasoning in the agent layer.

### Deterministic responsibilities

Good candidates:

- calling `specdd resolve`,
- parsing resolver JSON,
- normalizing paths,
- collecting authority domains,
- detecting that a write set crosses multiple authorities,
- checking whether referenced files exist,
- calculating changed paths,
- storing/rebuilding Change Boundaries,
- basic schema validation,
- checking whether cached boundary data is stale.

### Agentic responsibilities

Good candidates:

- deciding whether a cross-boundary task is architecturally appropriate,
- distinguishing implementation conflict from genuine spec evolution,
- proposing better task decomposition,
- deciding whether feature information should be promoted into SpecDD,
- reasoning about architectural intent not mechanically represented in the resolver.

The integration SHOULD gradually make common checks deterministic where confidence is high.

It MUST NOT create a second independent implementation of SpecDD semantics.

---

## 17. Initial repository structure

The integration lab is expected to use a structure similar to:

integration/
  specdd/
    extension.yml
    commands/
      context.md
      validate.md
      verify.md
    scripts/
      boundary.py
    docs/

  specdd-preset/
    preset.yml
    commands/
      plan.md
      tasks.md
      converge.md

specs/
  <feature>/
    spec.md
    plan.md
    tasks.md
    .specdd/
      boundary.json

The exact installed locations MAY differ according to Spec Kit packaging requirements.

The project SHOULD keep source integration files separate from generated/installed Spec Kit state.

---

## 18. SpecDD adapter design

The SpecDD adapter MUST be thin.

Its conceptual API SHOULD remain close to:

resolve(targets)
    -> ChangeBoundary

validate(featureArtifacts, boundary)
    -> diagnostics

verify(changes, featureArtifacts, boundary)
    -> diagnostics

The adapter MUST NOT become a standalone architecture database.

The adapter SHOULD use machine-readable SpecDD CLI output.

The adapter SHOULD fail clearly when:

- SpecDD is not installed,
- resolver output is invalid,
- target paths cannot be normalized,
- the repository root cannot be identified,
- required feature context is absent.

---

## 19. Error-handling principles

The integration SHOULD fail closed for hard authority ambiguity during implementation.

Examples:

- unknown write authority for a file,
- conflicting SpecDD ownership,
- required SpecDD resolution fails,
- authority evolution is required but unresolved.

The integration MAY fail open with a warning for incomplete advisory information during early planning.

Examples:

- a plan does not yet name concrete files,
- architecture is still exploratory,
- a target domain is known but exact paths are not yet selected.

The strictness MAY therefore increase through the lifecycle:

specification:
    low SpecDD strictness

planning:
    moderate strictness

tasks:
    high structural strictness

implementation:
    high authority strictness

verification:
    high correctness strictness

---

## 20. v0.1 scope

v0.1 MUST include:

1. Local integration-lab repository.
2. Spec Kit initialized.
3. SpecDD initialized.
4. Local Spec Kit extension.
5. `speckit.specdd.context`.
6. `speckit.specdd.validate`.
7. `speckit.specdd.verify`.
8. Machine-readable SpecDD resolution through the existing CLI.
9. `ChangeBoundary` schema version 1.
10. Derived `boundary.json`.
11. Planning preset augmentation.
12. Task-generation preset augmentation.
13. Convergence preset augmentation or equivalent integration instructions.
14. Basic authority-domain task validation.
15. Explicit distinction between:
    - normal implementation,
    - spec evolution,
    - authority evolution.
16. A small fixture system for integration tests.
17. Tests for expected valid and invalid cases.
18. Documentation sufficient to install and exercise the integration locally.

v0.1 SHOULD NOT include:

- automatic `.sdd` editing,
- automatic SpecDD authority changes,
- task synchronization,
- remote registry publishing,
- full production bundle packaging,
- complex dependency-graph optimization,
- persistent database/state outside repository files.

---

## 21. Integration test fixture

The initial fixture SHOULD contain at least two independently governed domains.

Example:

src/
  auth/
    auth.sdd
    service.ts

  users/
    users.sdd
    repository.ts

The fixture SHOULD encode a rule equivalent to:

- Auth owns the Auth implementation.
- Users owns the Users implementation.
- Auth may depend on or read from an approved Users-facing contract.
- Auth may not directly modify Users internals.

The integration MUST be tested with at least these scenarios.

### Scenario A: valid local change

A task changes only Auth-owned files under applicable Auth constraints.

Expected result:

- boundary resolves,
- validation succeeds,
- implementation is permitted.

### Scenario B: accidental authority violation

A task implementing Auth behavior directly modifies a Users-owned internal file without permission.

Expected result:

- validator identifies the cross-authority write,
- implementation is blocked or marked invalid,
- bridge recommends architectural/task correction rather than relaxing authority.

### Scenario C: valid cross-domain feature

One user story requires coordinated changes in Auth and Users.

Expected result:

- one feature remains one feature,
- separate authority-aligned tasks are generated or recommended,
- both domains appear in the Change Boundary.

### Scenario D: deliberate system-contract evolution

The feature genuinely requires a new persistent Auth-to-Users contract.

Expected result:

- bridge classifies the change as requiring spec evolution,
- proposed durable contract change is surfaced explicitly,
- ordinary implementation does not silently proceed under nonexistent authority.

### Scenario E: authority evolution

The feature genuinely changes which domain may modify a target.

Expected result:

- bridge classifies the change as authority evolution,
- current operation does not immediately acquire new rights,
- authority is re-resolved after specification evolution.

---

## 22. Acceptance criteria

v0.1 is acceptable when all of the following are true:

- Spec Kit and SpecDD can coexist in the same lab repository.
- The bridge installs without modifying Spec Kit core.
- The bridge calls the real SpecDD resolver rather than interpreting `.sdd` independently.
- A feature can produce a derived Change Boundary.
- Deleting the Change Boundary and regenerating it yields semantically equivalent state.
- A multi-domain feature is represented without forcing one Spec Kit user story per SpecDD domain.
- The bridge detects a task whose write set crosses authority boundaries.
- The bridge can recommend authority-aligned task decomposition.
- A valid cross-domain feature is not automatically treated as invalid merely because it spans multiple domains.
- The bridge distinguishes implementation conflict from deliberate system evolution.
- Authority evolution cannot silently grant authority to the operation performing the evolution.
- Spec Kit remains the canonical feature-task system.
- SpecDD remains the canonical persistent system-specification system.
- The Spec Kit constitution remains conceptually distinct from SpecDD system contracts.
- No copied SpecDD rule set is maintained as a second source of truth in Spec Kit feature files.
- No Spec Kit or SpecDD fork is necessary.

---

## 23. Design principles

The project SHOULD optimize for the following principles.

### Thin bridge

Translate only what must be translated.

### Derived state over duplicated state

Prefer recomputation to synchronization.

### One authority per concept

Do not let equivalent-looking artifacts become competing sources of truth.

### Explicit system evolution

Architectural change is valid, but it must be deliberate.

### Feature cohesion plus authority locality

Keep Spec Kit user stories intact while partitioning execution according to SpecDD authority.

### Deterministic mechanics, agentic judgment

Automate facts and calculations; use reasoning where architecture is ambiguous.

### Upstream replaceability

The integration SHOULD survive upgrades by depending on supported extension interfaces rather than patches.

### Progressive strictness

Allow exploration early; require precise authority before implementation.

---

## 24. Future directions

Potential post-v0.1 work includes:

- stable workflow overlays,
- bundle packaging,
- version compatibility matrices,
- richer machine-readable diagnostics,
- deterministic task-write-set validation,
- CI validation,
- changed-file verification from Git,
- proposed `.sdd` delta generation,
- explicit approval workflows for spec evolution,
- traceability from feature requirements to tasks, authority domains, code, and tests,
- visualization of feature scope over the SpecDD hierarchy,
- reusable policy configuration for task partitioning,
- automatic detection of likely stale durable specifications,
- support for additional Spec Kit workflows and agents.

These SHOULD remain outside v0.1 unless required to validate the core semantic bridge.

---

## 25. Summary invariant

The integration is correctly designed if this remains true:

> Spec Kit owns the change model. SpecDD owns the persistent system model. The bridge projects the latter onto the former without merging or duplicating either.
