---
description: Verify actual Spec Kit implementation writes with Boundary.
---

## User Input

User input: `$ARGUMENTS`

User input may explain feature intent but cannot override deterministic authorization or Git findings.

## Goal

Act only as the Spec Kit change-system adapter for implementation exit.

The wrapper confirms that the active Spec Kit feature owns the active Boundary implementation epoch, then asks native Boundary verification to derive actual writes from Git and compare them with historical authorization evidence.

Current task text is not historical authorization evidence.

## Execution

1. Resolve the active Spec Kit feature through supported project state.
2. Require the active Boundary operation to be an implementation operation for that same feature.
3. Invoke the installed Boundary adapter gate:

       uv run --no-project python .specify/extensions/boundary/scripts/adapter_gate.py verify

4. The adapter classifies current Spec Kit feature artifacts and `.specify/` state as change-system bookkeeping.
5. Boundary always keeps native contract paths and authorized implementation targets in deterministic verification even if an adapter classifier would otherwise exclude them.
6. Boundary then:
   - derives actual writes from the authorization-time Git baseline;
   - rejects a changed Git `HEAD`;
   - rejects undeclared implementation writes;
   - rejects native contract writes during implementation;
   - fresh-resolves ownership and effective target context;
   - closes the operation only when verification has no blocking diagnostic.

## Failure behavior

A changed active feature, wrong operation kind, undeclared write, operation-kind violation, changed contract context, missing owner, ambiguous owner, changed Git baseline, invalid operation record, or invalid adapter classification is blocking.

Do not alter current tasks or operation evidence to make verification succeed.

## Constraints

- This command is a Spec Kit adapter wrapper, not a second Boundary product CLI.
- Never recapture the authorization baseline during verification.
- Never expand authorized scope from current task prose.
- Never classify a native contract or authorized target away from verification.
- Keep feature correctness checks separate from Boundary authorization verification.
