## SpecDD Convergence Augmentation

Apply these requirements in addition to the upstream convergence pass. Preserve the upstream append-only `tasks.md`
contract and its feature-gap analysis.

1. Before deciding that the feature is converged, invoke `speckit.specdd.verify` through the active agent command
   mechanism. Verification must use the immutable authorization snapshot established before implementation together
   with its companion specification/control selections and authorization-time Git baseline. It must
   not use a freshly regenerated Change Boundary, current task text, or a recaptured baseline.
2. Keep deterministic SpecDD findings separate from upstream feature and constitution findings. Report a compact SpecDD
   subsection with the verification result, affected paths, and any pre-authorization dirty paths excluded by the Git
   baseline.
3. Recognize these system, governance, and authority diagnostic classes during convergence:
   - `SPECDD_VIOLATION`: the resulting SpecDD state fails deterministic checks such as `specdd lint`;
   - `SPECDD_DRIFT`: implementation scope is outside the authorized target set while remaining inside an already
     authorized authority domain;
   - `AUTHORITY_VIOLATION`: actual writes have unknown, conflicting, changed, or newly introduced authority;
   - `UNPLANNED_SPEC_EVOLUTION`: changed `.sdd` state was not selected by authorization-time evolution evidence;
   - `CONTROL_STATE_CHANGED`: an editable project bootstrap override changed after explicit authorization-time selection;
   - `CONTROL_STATE_VIOLATION`: immutable, unrelated, or unplanned root SpecDD control state changed;
   - `MISSING_SPEC_EVOLUTION`: agentic finding that implementation introduces a durable system contract future work
     must preserve but deliberate SpecDD evolution is absent.
4. Do not derive `MISSING_SPEC_EVOLUTION` merely from an unplanned file, a cross-boundary task, changed `.sdd` files,
   bootstrap-control findings, or a pre-authorization dirty path excluded by the Git baseline. Use the durable-contract
   promotion test from the project specification.
5. When a SpecDD finding requires remaining work, append a normal convergence task using the upstream task format and a
   source reference such as `SpecDD:AUTHORITY_VIOLATION`.
6. A blocking `SPECDD_VIOLATION`, `AUTHORITY_VIOLATION`, `UNPLANNED_SPEC_EVOLUTION`, or `CONTROL_STATE_VIOLATION`
   prevents a clean converged result even when feature behavior is otherwise complete.
7. Changed `.sdd` files, bootstrap-control files, refreshed Change Boundary state, or recaptured Git baseline state in
   the same operation never retroactively authorize implementation writes. Dependent implementation requires separate
   successful authorization after durable evolution.
