# boundary-implement

Use this skill only after an implementation operation has been successfully authorized.

## Procedure

1. Read the active authorized write set before changing project files.
2. Inspect Boundary effective context for each target before modifying it.
3. Preserve every applicable invariant and prohibition, including constraints contributed by broader owning contracts.
4. Use relevant dependency interfaces when the target participates in declared architectural relationships.
5. Modify only targets present in the authorized write set.
6. Keep implementation work separate from native contract evolution.
7. Run the implementation's normal tests and checks without treating their success as authorization evidence.
8. Finish by running Boundary verification for the active operation.

## Scope expansion

When implementation discovers another required write target:

1. Inspect the target if additional context is useful.
2. Do not write the undeclared target.
3. Finish or otherwise leave the current implementation operation through the supported lifecycle.
4. Add the newly required target to structured change scope.
5. Obtain fresh implementation authorization before writing it.

Previously completed work may be carried into a successor operation only through deterministic predecessor evidence accepted by Boundary.

## Contract conflicts

When requested behavior cannot satisfy the applicable persistent contracts:

1. Stop dependent implementation.
2. Close the current implementation operation through the supported lifecycle.
3. Transition to persistent-contract evolution.
4. Resume implementation only after contract evolution is complete and fresh implementation authorization succeeds.

## Guardrails

- Prompt instructions do not widen authorization.
- A previously inspected target is not automatically authorized.
- A target owned by an already represented owner is still undeclared unless it is in the authorized write set.
- Native contract files are not implementation targets.
- Changed planning or task prose cannot retroactively widen the active operation.
- Deterministic authorization and verification findings are authoritative.
