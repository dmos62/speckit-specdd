## SpecDD Planning Augmentation

Apply these requirements in addition to the upstream planning workflow. They do not replace any upstream planning step or Constitution Check.

1. After the plan identifies concrete or intended implementation paths, invoke `speckit.specdd.context` through the active agent command mechanism. Prefer explicit target paths from the plan; otherwise let the bridge discover exact targets from the active feature artifacts. Do not derive targets from symbols, similar names, or architectural guesses.
2. Read the resulting feature `.specdd/boundary.json` and add or refresh a concise `## SpecDD Impact` section in `plan.md`. Record only:
   - the boundary path,
   - resolved target paths,
   - primary authority domains,
   - `crossBoundary`,
   - unresolved diagnostic codes and paths.
3. Do not copy `Must`, `Must not`, `Owns`, or `Can modify` entries into the plan. The Change Boundary and `.sdd` hierarchy remain authoritative.
4. Use the projection to shape the implementation approach. One feature may span multiple SpecDD domains, but planned writes should stay authority-local where practical and cross-domain interaction should use the governed contracts already exposed by those domains.
5. Distinguish ordinary implementation from work that appears to require `SPEC_EVOLUTION_REQUIRED` or `AUTHORITY_EVOLUTION_REQUIRED`. A multi-domain feature by itself is not evidence that either evolution class applies.
6. During planning, unresolved targets are advisory because exact paths may still be emerging. Record the uncertainty in `## SpecDD Impact`; never convert unresolved context into authority.
7. If authority evolution is anticipated, state that the authority-changing spec edit is a separate operation and that implementation relying on the new authority requires a fresh Change Boundary afterward.
