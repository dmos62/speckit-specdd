# Native Contract Semantics

Boundary uses a native persistent-contract model designed for deterministic scope resolution and concise progressive agent context.

The native model intentionally preserves the useful property of hierarchical constraints without inheriting SpecDD's file-location and framework-bootstrap semantics.

## Canonical location

Native contracts live under:

    contracts/**/*.contract.md

A contract file's directory has no semantic meaning.

Moving a contract file without changing its ID or declared scopes must not change which implementation targets it governs.

## Contract form

Boundary v1 uses Markdown with YAML frontmatter.

Example:

    ---
    schema: boundary.contract/v1
    id: payments

    owns:
      - src/payments/**

    applies_to:
      - src/api/payment-methods/**

    depends_on:
      - users
    ---

    # Payments

    ## Purpose

    Own payment processing and payment-provider integration.

    ## Invariants

    - Raw card data is never persisted.
    - Provider-specific details remain behind the payment-provider interface.

    ## Prohibitions

    - Payment code must not depend on user persistence internals.

    ## Interfaces

    - Consumers use the public payment-provider interface.

Only the frontmatter carries deterministic scope and graph semantics.

Markdown sections carry human-readable architectural intent.

## Required fields

Every contract has:

- `schema`;
- stable `id`.

A contract must declare at least one of:

- `owns`;
- `applies_to`.

`owns` and `applies_to` are arrays of explicit repository scopes.

`depends_on` is optional and contains contract IDs.

Boundary v1 deliberately has no `extends`, `override`, `except`, `Can modify`, or equivalent delegated-write field.

## Path scope grammar

Boundary v1 supports only two ownership/applicability forms:

- an exact repository-relative path;
- a subtree path ending in `/**`.

Examples:

    src/auth/service.ts
    src/auth/**
    docs/api/**

The following are not Boundary v1 scope syntax:

    **
    src/*/service.ts
    src/{auth,users}/**
    src/**/generated/*.ts

Restricting the grammar makes intended-target behavior independent of filesystem existence and keeps containment mechanically decidable.

An exact path is always exact.

A subtree path always denotes that subtree whether or not the directory exists yet.

No probe file or resolver capability is needed.

## No global catch-all contract

Boundary v1 does not support a repository-wide catch-all scope.

In particular, `**` is invalid.

Cross-component or cross-layer constraints must identify the concrete scopes to which they apply.

Development-process rules that truly apply to every change belong in change-system governance or stable Boundary procedure, not in a global persistent architecture prompt.

This prevents a new monolithic project contract from replacing the old framework bootstrap.

## Applicability

A contract applies to every target matched by either:

- one of its `owns` scopes;
- one of its `applies_to` scopes.

All matching contracts are applicable.

Applicability is additive.

There is no nearest-contract-wins rule.

A more specific contract cannot erase a broader matching contract by omission.

## Nested ownership

Ownership may be nested when scopes are strictly contained.

For example:

    payments owns src/payments/**
    stripe owns src/payments/providers/stripe/**

For:

    src/payments/providers/stripe/client.ts

the primary owner is `stripe`.

Both `payments` and `stripe` remain applicable because both ownership scopes match.

The effective context therefore contains the broader Payments constraints plus the more specific Stripe constraints.

This preserves hierarchical constraint propagation without coupling semantics to contract-file placement.

## Ownership ambiguity

A target must have one unambiguous most-specific owner.

With Boundary v1's restricted path grammar, ownership scopes can be compared structurally.

The contract graph is invalid when matching ownership scopes overlap without one being strictly more specific than the other, or when equally specific scopes claim the same target.

Authorization fails for an unowned or ambiguously owned implementation target.

## No override semantics in v1

Applicable contract semantics are monotonic.

More specific contracts may add requirements but cannot explicitly cancel broader requirements.

Boundary v1 does not provide an exception mechanism.

If a broad rule is no longer correct for a subtree, contract evolution must change the contract structure or narrow the original scope deliberately.

This keeps weakening of architectural constraints visible.

## Cross-component contracts

Boundary does not use a global cross-contract file.

A durable relationship spanning components may instead use a narrowly scoped relationship contract.

For example:

    ---
    schema: boundary.contract/v1
    id: auth-user-identity

    applies_to:
      - src/auth/**
      - src/users/identity.ts

    depends_on:
      - auth
      - users
    ---

Such a contract has no ownership role unless it also declares `owns`.

Its prose can describe only the relationship that needs to remain durable.

Because its applicability is explicit, the contract appears only when work touches its relevant scopes.

## Dependencies

`depends_on` identifies architectural dependencies between contract IDs.

For normal target context, Boundary exposes the depended-on contract's `Interfaces` section and source provenance rather than automatically importing all of its internal invariants.

If a rule from another component must directly constrain the caller, that relationship should be represented through explicit `applies_to` scope or a dedicated relationship contract.

This avoids accidental transitive expansion of agent context.

## Semantic sections

Boundary v1 recognizes these conventional Markdown sections:

- `Purpose`;
- `Invariants`;
- `Prohibitions`;
- `Interfaces`.

The engine may preserve other sections for raw inspection, but only recognized sections participate in the standard effective-context projection.

Boundary does not attempt to prove arbitrary prose mechanically.

Structure determines when semantic material is relevant. Prose explains what it means.

## Effective target context

For target `T`, Boundary derives:

1. the most-specific unambiguous owner;
2. every contract whose `owns` or `applies_to` scope matches `T`;
3. the recognized semantic sections from those contracts;
4. relevant `Interfaces` sections from directly declared dependencies;
5. exact source provenance and content identities.

Collections are normalized and ordered deterministically.

The result is disposable query output.

It is not written back into feature artifacts or stored as another persistent contract representation.

## Structural validation

`boundary contracts check` must deterministically validate at least:

- frontmatter syntax and schema version;
- unique contract IDs;
- canonical repository-relative scopes;
- allowed scope grammar;
- prohibition of catch-all `**`;
- ownership nesting and ambiguity;
- existence of declared dependency IDs;
- dependency self-reference;
- deterministic contract discovery;
- recognized section extraction.

Additional checks should be added only when their semantics are precise.

## Deliberately omitted v1 concepts

Boundary v1 does not preserve these SpecDD concepts automatically:

- framework bootstrap inheritance;
- directory-position semantics;
- arbitrary ownership glob syntax;
- `Can modify`;
- task entries inside persistent contracts;
- global root contract inheritance;
- provider framework versions.

If a concrete Boundary use case later requires delegated non-owner write permission, it should be introduced as a native owner-issued concept rather than copied from the legacy provider by default.
