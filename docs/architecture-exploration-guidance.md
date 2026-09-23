# Agent Instruction Architecture Exploration

## Purpose

This document is a guide for examining how the system should present instructions, contracts, workflow guidance, and authority information to coding agents.

It is intentionally exploratory rather than prescriptive.

The system has evolved since the ideas captured here were first discussed. Those earlier ideas may no longer match the current architecture, terminology, lifecycle, tooling, or constraints. Treat them as hypotheses worth testing against the current implementation, not as a design to recover.

A particularly important shift is that SpecDD is no longer intended to be a central product concept. It may remain useful as an inspiration, a source of semantics, or a current implementation dependency, but the bridge should not require users or agents to understand the system in SpecDD terms. Its name should not define the product model or the agent-facing architecture.

## Starting posture

Begin by learning the system that exists now.

Do not assume that any of the following are still true:

- `.specdd/bootstrap.md` is an important agent input.
- `.sdd` files are the primary or only persistent contract format.
- the current resolver model is the right abstraction to expose to agents.
- the previous `context → validate → authorize → implement → verify` flow is still the lifecycle to preserve.
- implementation and contract evolution should use exactly two agent modes.
- existing Spec Kit commands, hooks, skills, or generated artifacts have the same responsibilities they had previously.
- the old bridge boundaries are still the right architectural boundaries.
- current agent integrations discover or invoke skills in the same way.
- the best solution is a smaller version of the old prompt.

The first objective is to identify what the present system already does well, what responsibilities are duplicated, and where agent context is carrying information that could instead be derived, retrieved, or enforced mechanically.

## Core question

The broad design question is:

> What is the smallest, clearest, most portable set of information an agent needs at each point in the workflow, and what should instead live in tools, generated state, project contracts, or on-demand skills?

This can be investigated without committing to any particular file layout, naming scheme, prompt format, or contract language.

## Explore the current instruction surface

Inventory every place from which an agent can currently receive behavioral guidance or project context.

Look for categories such as:

- system or harness instructions;
- repository-level agent instructions;
- Spec Kit-generated command or skill instructions;
- extension or preset material;
- workflow hooks and structural gates;
- project contracts or specifications;
- generated boundary, scope, authority, or verification state;
- tool output inserted into context;
- files included automatically by iteration tooling;
- skills or other discoverable on-demand capabilities;
- integration-specific materializations for Codex, Claude, or other agents.

For each source, ask:

- Is it always loaded, conditionally loaded, or pulled on demand?
- Is it stable across many turns or regenerated frequently?
- Does it describe policy, procedure, facts, or enforcement?
- Is the information canonical or derived?
- Could the agent safely operate without seeing it?
- Does another layer already enforce the same rule?
- Is the content specific to one agent vendor or portable?
- Does the same concept appear in multiple instruction surfaces?

The goal is not merely to reduce tokens. It is to understand whether each piece of information is in the correct layer.

## Separate four kinds of concerns

A useful lens is to distinguish four kinds of material. The current system may use different names or combine some of these, so treat this as an analytical model rather than a required architecture.

### Always-on policy

These are rules the agent should not have to decide whether to load.

Possible examples include:

- which artifact owns feature intent;
- whether generated state is canonical;
- whether agents may infer write authority;
- whether contract changes and implementation changes are distinct operations;
- whether authorization can be widened retroactively.

If such rules exist, examine whether they can be expressed in a very small, stable, cache-friendly instruction prefix.

### Procedural capability

These are instructions for performing a recognizable kind of work.

Examples might include:

- implementing within an authorized scope;
- handling newly discovered write targets;
- evolving persistent contracts;
- investigating an authority conflict;
- recovering from failed verification.

These are candidates for discoverable skills or equivalent on-demand capabilities, especially when they are only relevant during certain workflow stages.

### Operation-specific facts

These are facts about the current feature or operation, for example:

- concrete targets;
- current owners;
- allowed modifiers;
- effective constraints;
- unresolved scope;
- authorization state;
- validation findings;
- changed files.

These are usually better generated or retrieved than embedded in stable instructions.

### Deterministic enforcement

These are checks that should not depend on the model remembering or correctly interpreting prose.

Examples might include:

- path normalization;
- ownership calculation;
- scope validation;
- freshness checks;
- write authorization;
- contract syntax validation;
- verification of actual changed files.

When deterministic enforcement exists, consider whether corresponding explanatory prompt text can be shortened to behavioral guidance rather than re-describing the algorithm.

## Investigate skills as a delivery mechanism

Skills are worth evaluating because they can provide progressive disclosure: an agent can know that a capability exists without loading its full instructions until needed.

Do not begin by deciding that a specific set of skills must exist. Instead, inspect the current workflow and identify coherent procedures that:

- recur across features;
- require agent judgment;
- are not purely deterministic;
- have a clear trigger;
- can be described independently of one vendor's tool syntax;
- would otherwise bloat always-on instructions.

Possible capability boundaries to test include:

- implementation under current contracts and scope;
- contract or architecture evolution;
- scope expansion after discovering additional necessary targets;
- interpretation or remediation of validation and verification findings.

The earlier idea of separate implementation and contract-evolution skills remains a useful hypothesis, but the current system may suggest different boundaries.

For each potential skill, ask:

- Can an agent recognize when to use it from a short description?
- Is its procedure stable enough to cache?
- Does it need supporting reference material?
- Does it depend on one particular agent runtime?
- Does it duplicate lifecycle commands or deterministic gates?
- Would splitting it further improve clarity, or merely increase skill-selection ambiguity?

## Keep lifecycle orchestration distinct from agent skills

Examine whether the current system cleanly distinguishes:

- lifecycle orchestration;
- agent behavior;
- deterministic validation and enforcement.

A skill should generally explain how an agent behaves during a kind of work. It should not become the sole enforcement mechanism for authority or safety-critical workflow constraints.

Likewise, a lifecycle command or workflow gate need not become a skill merely because an agent can invoke it.

A useful conceptual distinction to test is:

- lifecycle layer: what stage of work is happening;
- skill layer: how the agent should reason and behave during that kind of work;
- enforcement layer: what the system computes and rejects deterministically.

The present architecture may implement these boundaries differently. The goal is to find a clean separation, not to preserve old labels.

## Reconsider what raw contract material the agent needs

One earlier direction was to avoid giving the implementation agent a large framework prompt plus all raw project contracts, and instead provide a derived effective view.

That idea is still worth testing, but should not be assumed correct.

Explore whether the current system could provide an operation-specific projection containing only information such as:

- target path;
- governing contract or owner;
- applicable modification permission;
- relevant required behavior;
- relevant prohibitions;
- relevant dependencies;
- unresolved or ambiguous conditions;
- provenance or fingerprints needed for trust.

Then compare this with giving the agent the raw source contracts.

Questions to answer:

- Does a derived view preserve enough semantic nuance?
- Can provenance remain inspectable when the agent needs to understand why a rule applies?
- Can shared constraints be deduplicated across targets?
- Does the agent need raw contracts only during contract-authoring work?
- Can the derived representation be generated deterministically?
- Does generating it accidentally create a second persistent source of truth?

Do not assume JSON is the right representation. The best format may be structured data, concise prose, a tool result, or a hybrid.

## Treat SpecDD as an implementation detail, not a product concept

Audit the current architecture for places where SpecDD terminology leaks into the user-facing or agent-facing model.

Examples may include:

- command names;
- skill names;
- generated field names;
- workflow stages;
- diagnostics;
- documentation;
- directories;
- environment variables;
- product explanations.

For each occurrence, distinguish between:

1. an implementation dependency that can remain internal;
2. a durable semantic concept the product still needs;
3. historical naming that should eventually disappear.

Try to express the product concepts without referring to SpecDD.

For example, the enduring concepts may be closer to:

- persistent project contracts;
- ownership;
- modification permission;
- effective constraints;
- operation scope;
- authorization evidence;
- contract evolution;
- implementation verification.

Those concepts may still be implemented today using parts of the SpecDD CLI or file format. That does not require the user-facing model to inherit the implementation's name.

Avoid renaming mechanically. First identify which concepts genuinely survive once SpecDD terminology is removed.

## Explore cache-friendly context composition

Caching should influence instruction architecture, but should not override correctness.

Investigate whether context can be ordered from most stable to most volatile:

1. generic agent instructions;
2. stable product or repository rules;
3. stable skill instructions when invoked;
4. project-level durable context;
5. operation-specific effective contracts;
6. feature and task state;
7. authorization or verification state;
8. relevant source and tests;
9. the immediate user request or latest findings.

Look for avoidable cache invalidators in stable material, such as:

- timestamps;
- feature identifiers;
- hashes;
- current target lists;
- dynamically generated diagnostics;
- integration-specific paths;
- volatile environment details.

Where generated context is needed, prefer deterministic output:

- stable field ordering;
- normalized paths;
- normalized whitespace;
- no timestamps unless semantically required;
- no random identifiers;
- stable ordering where ordering is not itself meaningful.

Measure actual context and cache behavior if the current agent platform makes that possible rather than relying only on intuition.

## Examine portability across agent runtimes

The system should ideally separate canonical workflow semantics from agent-specific packaging.

Investigate:

- which agents support discoverable skills;
- what common skill format can be shared;
- which frontmatter or directory conventions are vendor-specific;
- how Spec Kit currently materializes commands and skills for different integrations;
- whether agent-specific wrappers can remain thin.

Prefer canonical skill content that uses product-level concepts rather than vendor-specific tool calls.

For example, instructions such as “refresh operation scope” or “run authorization” are more portable than instructions naming a particular runtime function.

Agent-specific materialization can map those concepts onto the actual local commands or tools.

Do not assume full portability is possible. Document where the abstraction leaks and decide whether those differences belong in packaging, wrappers, or canonical instructions.

## Explore scope expansion during implementation

One behavior worth preserving in some form is the ability to discover necessary work during implementation without silently widening authority.

Study how the current system handles this today.

A desirable property to test is:

- an agent may discover an additional target;
- discovery itself is allowed;
- the target is not modified under stale scope;
- the system can expand or replace the active authorization through an explicit lifecycle transition;
- already completed valid work does not necessarily need to be discarded;
- verification uses the final valid authority context.

The exact mechanism may differ substantially from the earlier design. It could be task regeneration, an operation update, a nested authorization, a new workflow run, or something else.

The key question is whether scope can evolve safely without making ordinary coding unnecessarily brittle.

## Explore contract evolution as a first-class transition

Similarly, investigate how the present system represents the case where requested implementation cannot satisfy existing persistent contracts.

Questions include:

- How does the agent recognize a contract mismatch?
- Is there a clear transition from implementation work to contract evolution?
- Does contract evolution invalidate current implementation authority?
- Is fresh resolution or authorization required afterward?
- What instructions become available during contract authoring?
- Can implementation files remain untouched during that operation?
- How are partially completed implementation changes handled?

The earlier proposal used a separate on-demand skill for contract evolution. Keep that as one option, not a requirement.

## Reduce duplicated explanations

Search for cases where the same rule is represented in several places, for example:

- repository instructions;
- command prompts;
- skill bodies;
- project contracts;
- workflow documentation;
- generated diagnostics.

For each duplicated rule, decide which layer should own it.

A useful preference is:

- policy lives in one stable instruction source;
- project semantics live in persistent contracts;
- procedure lives in a skill or lifecycle command;
- facts live in generated operation state;
- enforcement lives in deterministic code;
- documentation explains the system but does not secretly become another authority source.

Duplication may sometimes be intentional for usability. The question is whether repeated text creates competing sources of truth or unnecessary context cost.

## Potential experiments

Before restructuring the system broadly, consider small experiments that reveal whether the model behaves better with a different instruction architecture.

### Remove the large framework prompt from implementation context

Keep existing resolver and validation behavior unchanged, but stop injecting the old framework bootstrap into normal implementation iterations.

Observe:

- whether agents still make correct authority decisions;
- which missing information they actually need;
- whether they request raw contracts;
- whether verification catches meaningful regressions.

### Introduce one narrowly scoped implementation skill

Create a small skill for working within current operation scope and handling newly discovered targets.

Do not redesign the rest of the system yet.

Observe:

- whether agents discover and invoke it reliably;
- whether its description is sufficient for self-selection;
- whether instructions currently duplicated elsewhere can be removed.

### Make contract-authoring guidance on demand

Move detailed contract-writing guidance out of normal implementation context and expose it only during explicit contract evolution.

Observe:

- context reduction;
- contract-edit quality;
- lint failures;
- whether agents need more semantic reference material than expected.

### Compare raw and derived contract context

Run representative tasks with:

- raw governing contracts;
- a concise effective projection;
- both.

Compare correctness, explainability, token use, cache behavior, and failure modes.

### Test multiple agent integrations

Materialize the same canonical capability into at least two agent runtimes.

Record:

- what remained portable;
- what needed wrappers;
- whether skill discovery behavior differed;
- whether stable context ordering could remain the same.

## Evaluation criteria

Any new instruction architecture should be judged on more than prompt size.

Consider:

- correctness of implementation;
- preservation of project contracts;
- authority enforcement;
- ability to recover from newly discovered scope;
- clarity of lifecycle transitions;
- amount of always-loaded context;
- cache stability;
- deterministic reproducibility;
- portability across agent runtimes;
- ease of debugging agent mistakes;
- provenance of generated constraints;
- maintainability of canonical instructions;
- ease of evolving or replacing the current contract engine;
- degree to which implementation details leak into the product model.

## Warning signs

Be cautious if a proposed redesign:

- replaces one large bootstrap with another large always-loaded prompt;
- makes agent compliance the only enforcement layer;
- requires the agent to manually reproduce deterministic ownership or scope calculations;
- introduces a second persistent copy of project contracts;
- makes current SpecDD terminology part of the new product abstraction merely because the implementation still uses it;
- creates many overlapping skills with ambiguous triggers;
- puts volatile operation data into otherwise stable skill files;
- couples canonical instructions to one agent vendor;
- hides provenance so thoroughly that users cannot understand why a constraint applies;
- makes normal implementation unable to adapt when additional work is discovered.

## Suggested investigation sequence

A practical investigation could proceed in this order:

1. Map the current lifecycle, instruction sources, generated state, and enforcement points.
2. Measure what context is actually delivered to the agent at each major stage.
3. Identify duplicated responsibilities and vocabulary inherited from the older SpecDD-centered architecture.
4. Separate always-on policy, procedural guidance, operation facts, and deterministic enforcement.
5. Identify one or two candidate skills based on real workflow boundaries.
6. Test removing unnecessary framework/reference material from normal implementation context.
7. Evaluate whether an effective contract projection improves clarity without losing important semantics.
8. Test contract evolution as a separate on-demand instruction mode.
9. Test materialization across more than one agent runtime.
10. Only then decide on naming, canonical file layout, migration strategy, and removal of old compatibility structures.

The order is deliberately investigative. Findings from the first few steps may invalidate the later ideas.

## Questions the review should answer

By the end of the exploration, the team should be able to answer:

- What information must every agent always know?
- What information should be discoverable but loaded only on demand?
- What information should be generated per operation?
- What should never be entrusted to prompt-following alone?
- What are the real product concepts after removing SpecDD terminology?
- Which current SpecDD-derived semantics are worth preserving?
- Which are implementation artifacts that can eventually disappear?
- What is the canonical source for each kind of rule or state?
- How does an agent safely expand implementation scope?
- How does an implementation transition into contract evolution?
- How does the system resume after contract evolution?
- Which instruction artifacts can remain byte-stable for effective caching?
- How much of the architecture is portable across agent runtimes?
- Where do vendor-specific adaptations belong?
- Can the current contract engine be replaced later without redesigning the agent-facing workflow?

## Desired outcome

The goal is not to produce a “SpecDD-lite” prompt.

The stronger outcome would be an agent architecture in which:

- persistent project contracts exist independently of any one agent;
- the current contract engine can remain an implementation detail;
- agents receive only the guidance and facts relevant to the work they are doing;
- procedural knowledge can be discovered on demand;
- deterministic mechanisms enforce authority and structural correctness;
- stable instructions remain small and cache-friendly;
- lifecycle orchestration remains understandable;
- implementation details do not dominate product terminology;
- future replacement of current SpecDD-derived components is possible without invalidating the overall interaction model.

The current system should determine how much of this vision survives contact with reality.