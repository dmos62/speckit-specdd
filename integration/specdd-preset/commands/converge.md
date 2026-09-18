## SpecDD Convergence Augmentation

Apply these requirements in addition to the upstream convergence pass. Preserve the upstream append-only `tasks.md`
contract and its feature-gap analysis.

1. Before deciding that the feature is converged, invoke `speckit.specdd.verify` through the active agent command
   mechanism. Verification must use the immutable authorization snapshot established before implementation, not a
   freshly regenerated Change Boundary.
2. Keep deterministic SpecDD findings separate from upstream feature and constitution findings. Report a compact SpecDD
   subsection with the verification result and affected paths.
3. Recognize these system/authority diagnostic classes during convergence:
   - `SPECDD_VIOLATION`: the resulting SpecDD state fails deterministic checks such as `specdd lint`;
   - `SPECDD_DRIFT`: implementation scope is outside the authorized target set while remaining inside an already
     authorized authority domain;
   - `AUTHORITY_VIOLATION`: actual writes have unknown, conflicting, changed, or newly introduced authority and cannot
     be accepted under the authorization snapshot;
   - `MISSING_SPEC_EVOLUTION`: agentic finding that the implementation introduces a durable system contract future work
     must preserve but deliberate SpecDD evolution is absent.
4. Do not derive `MISSING_SPEC_EVOLUTION` merely from an unplanned file, a cross-boundary task, or the presence of
   changed `.sdd` files. Use the durable-contract promotion test from the project specification.
5. When a SpecDD finding requires remaining work, append a normal convergence task using the upstream task format and a
   source reference such as `SpecDD:AUTHORITY_VIOLATION`. Keep feature intent intact; recommend implementation
   correction before spec evolution unless the behavior genuinely requires durable contract evolution.
6. A blocking `SPECDD_VIOLATION` or `AUTHORITY_VIOLATION` prevents a clean converged result even when feature behavior
   is otherwise complete. Do not relax authority as the remediation.
7. Changed `.sdd` files or refreshed Change Boundary state in the same operation never retroactively authorize
   implementation writes. Dependent implementation requires a separate successful authorization after evolution.
