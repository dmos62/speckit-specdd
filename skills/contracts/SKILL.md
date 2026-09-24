# boundary-contracts

Use this skill for deliberate evolution of persistent Boundary contracts.

## Procedure

1. Identify the durable system rule, ownership statement, applicability rule, or interface that actually needs to change.
2. Confirm that persistent-contract evolution is necessary rather than using it to accommodate an ordinary implementation mistake.
3. Inspect the existing contract graph and relevant effective context before editing contracts.
4. Make the smallest durable contract change that expresses the intended system semantics.
5. Preserve additive applicability: more-specific ownership does not remove broader applicable constraints.
6. Keep ownership and additional applicability explicit.
7. Declare architectural dependencies only when the relationship is durable and useful to downstream target context.
8. Modify only native contract files during the contract-evolution operation.
9. Run the Boundary structural contract check after editing.
10. Verify and close contract evolution before dependent implementation begins.
11. Require fresh implementation authorization against the resulting canonical contract graph.

## Contract design

Prefer:

- narrowly scoped contracts;
- concise invariants and prohibitions;
- explicit ownership;
- explicit additional applicability;
- focused dependency interfaces;
- durable system semantics that future work must preserve.

Avoid:

- repository-wide catch-all contracts;
- implicit override semantics;
- duplicating transient feature intent;
- generated operation facts;
- workflow state;
- rules that merely restate implementation details without durable value.

## Guardrails

- Contract evolution never retroactively authorizes implementation writes.
- Do not combine implementation changes with contract changes in one operation.
- Do not weaken contracts automatically to make implementation pass.
- Structural validation establishes graph correctness, not semantic correctness of prose.
- Dependent implementation always starts from a fresh authorization epoch.
