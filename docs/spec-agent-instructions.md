# Agent Instruction Architecture

Boundary uses progressive disclosure so agent context contains stable procedure plus only the project facts relevant to the current work.

The architecture deliberately avoids replacing `.specdd/bootstrap.md` with another large always-loaded instruction file.

## Instruction classes

Boundary separates four kinds of information.

### Stable Boundary policy

A very small set of product invariants may always be available:

- persistent contracts are canonical system constraints;
- applicable contracts are additive;
- implementation may not write undeclared targets;
- contract evolution is separate from dependent implementation;
- deterministic authorization and verification are authoritative.

This material should remain small, stable, and cache-friendly.

It does not contain project-specific contracts.

### Procedural skills

Reusable agent procedure lives in canonical Boundary skills.

Skills contain no current feature IDs, target paths, hashes, owners, tool versions, or generated operation state.

### Operation facts

Current facts are derived on demand:

- declared writes;
- target owner;
- applicable contracts;
- relevant invariants and prohibitions;
- dependency interfaces;
- authorization status;
- verification findings.

These belong in deterministic tool output rather than stable skill text.

### Deterministic enforcement

Scope, ownership, Git state, and operation-kind rules are enforced by code.

Skills explain how an agent should behave around those mechanisms but are not the security or correctness boundary.

## Canonical skills

Boundary v1 defines three procedural capabilities.

### `boundary-scope`

Use while planning implementation or refining tasks.

Responsibilities:

- identify exact intended write targets;
- distinguish implementation writes from contract evolution;
- query effective context for candidate targets;
- record explicit write declarations in the active change system;
- prefer owner-local task decomposition when it improves coherence;
- keep legitimate coordinated multi-owner work representable;
- avoid treating exploratory path mentions as authorization scope.

This skill does not authorize implementation.

### `boundary-implement`

Use when implementation begins under a successful authorization.

Responsibilities:

- inspect relevant effective context before changing a target;
- work only within the current authorized write set;
- preserve broader and more-specific applicable constraints;
- stop before writing an undeclared target;
- initiate the explicit scope-expansion lifecycle when additional work is discovered;
- recognize when requested behavior cannot satisfy current persistent contracts.

This skill does not alter authorization evidence.

### `boundary-contracts`

Use for deliberate persistent-contract evolution.

Responsibilities:

- identify the smallest durable contract change;
- preserve additive scope semantics;
- modify only contract files in the contract-evolution operation;
- run structural contract validation;
- avoid implementation writes during the same operation;
- require fresh implementation authorization afterward.

This skill is not loaded during ordinary implementation unless the operation transitions to contract evolution.

## Skill source and materialization

Canonical skill procedure is stored as plain Markdown in:

    skills/scope/SKILL.md
    skills/implement/SKILL.md
    skills/contracts/SKILL.md

Canonical files contain Boundary procedure only. They contain no runtime discovery frontmatter or runtime-specific paths.

The concrete Codex adapter at `adapters/codex/materialize.py` produces:

    .agents/skills/boundary-scope/SKILL.md
    .agents/skills/boundary-implement/SKILL.md
    .agents/skills/boundary-contracts/SKILL.md

The concrete Claude Code adapter at `adapters/claude/materialize.py` produces the same named skills under `.claude/skills/`.

Each materialized file consists only of fixed runtime discovery metadata followed by the canonical skill bytes. Materialization is deterministic and idempotent: unrelated feature, task, authorization, or operation state cannot alter generated skill bytes.

Generated materializations are not canonical source.

The two concrete adapters intentionally do not share a generalized runtime-provider framework. The second implementation is maintained as portability evidence while concrete differences remain small.

## Effective-context query

Boundary provides an on-demand query conceptually equivalent to:

    boundary inspect <target>

The agent-oriented representation should include only relevant facts, for example:

    Target: src/payments/providers/stripe/client.ts
    Owner: stripe

    Applicable contracts:
    - payments
    - stripe
    - payment-data-handling

    Invariants:
    - ...
    - ...

    Prohibitions:
    - ...

    Dependency interfaces:
    - ...

    Sources:
    - contracts/payments.contract.md
    - contracts/stripe.contract.md

Every projected semantic item retains provenance.

Agents may request the raw canonical contract when the projection is insufficient.

## Legacy bootstrap independence

Boundary installation and normal operation do not initialize or require `.specdd/bootstrap.md` as an agent-instruction source.

During migration, the temporary SpecDD compatibility adapter may continue to resolve legacy `.sdd` contracts directly for parity and compatibility work. That does not make SpecDD framework bootstrap text part of Boundary policy, skill procedure, or project contract context.

Existing bootstrap files in an older repository are legacy compatibility state. Boundary does not copy their instructions into another global prompt.

## No automatic full-contract loading

Normal implementation must not automatically load:

- every project contract;
- all dependency contracts recursively;
- legacy SpecDD bootstrap text;
- `.sdd` framework instructions;
- generated authorization records;
- historical feature artifacts unrelated to the operation.

A contract is loaded because its scope or direct dependency relationship makes it relevant.

## No global project contract in always-on context

Boundary v1 does not solve cross-component semantics by maintaining one global contract file that every agent always sees.

Durable cross-component rules use explicit scoped relationship contracts.

Development-process rules belong to the change system or stable Boundary procedure.

This keeps project architecture progressively disclosed and prevents a new context monolith.

## Context ordering

Where an agent runtime permits ordering, Boundary context should progress from stable to volatile:

1. generic agent/runtime instructions;
2. small stable Boundary policy;
3. invoked Boundary skill;
4. effective project contract context;
5. change/task state;
6. active authorization facts;
7. relevant source/tests;
8. immediate user request and latest findings.

Volatile identifiers and hashes must not be placed in stable skill files.

## Adapter portability

Canonical skills use product-level verbs such as:

- inspect target context;
- declare write scope;
- authorize implementation;
- verify operation;
- evolve contracts.

They do not require a specific agent function name or change-system command.

A concrete runtime adapter may add discovery metadata or map those verbs to local invocation syntax.

Differences that cannot be abstracted cleanly remain in the concrete adapter rather than leaking into canonical skill content.

## Failure behavior

When deterministic tooling reports an unresolved owner, undeclared target, invalid contract graph, or stale operation:

- the agent does not infer permission;
- the skill directs the agent to the appropriate lifecycle transition;
- the runtime remains the blocking authority.

Prompt wording must never convert a deterministic failure into permission.

## Evaluation criteria

The instruction architecture is tested for:

- canonical skills remaining small and runtime-neutral;
- concrete runtime discovery materialization;
- preservation of the exact canonical procedure beneath runtime frontmatter;
- stable materialized skill bytes across unrelated operations;
- implementation staying within explicit write scope;
- reliable scope-expansion behavior;
- correct transition to contract evolution;
- preservation of broader applicable constraints;
- reduced always-loaded context;
- clear provenance when a projected rule is questioned;
- concrete portability through Codex and Claude Code materialization without generalized adapter machinery.
