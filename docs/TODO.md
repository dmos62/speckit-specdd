# Spec Kit × SpecDD Integration Implementation Plan

Status: Planned
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Current baseline

The v0.1 semantic bridge is implemented. Current working-tree evidence from 2026-09-17 passes repository bootstrap check, all 88 tests, the real two-domain fixture lint, `git diff --check`, clean worktree status, and the tracked-file ignore-policy check.

Compatibility remains pinned to Node.js 22+, Spec Kit `1.0.7`, SpecDD CLI `1.1.1`, and SpecDD framework `1.5`. The exercised development host is Windows 10 `10.0.19045` on AMD64 with Node.js `v22.14.0` and Python `3.12.11`.

The remaining release gate is reproduction from a clean clone of committed repository state.

`dev-scripts.include` now exercises that gate automatically after the normal working-tree checks. The clean-clone check:

- clones committed `HEAD` into a temporary repository with `git clone --no-local`;
- prints the exact source commit;
- runs `bash scripts/bootstrap.sh`;
- reruns `bash scripts/bootstrap.sh --check`;
- runs the full unittest suite;
- runs the real SpecDD fixture lint;
- runs `git diff --check`;
- requires clean `git status --short`;
- requires that no tracked files are matched by repository ignore rules;
- removes the temporary clone afterward.

Bootstrap output supplies the exact Node.js, Python, Spec Kit, platform, architecture, and SpecDD version evidence for that run.

Do not mark clean-clone reproduction complete until a subsequent programming iteration reports `clean-clone acceptance: PASS`.

## 15. Phase 15 — v0.1 hardening

### TODO

- [ ] Re-run all acceptance scenarios from a clean clone. The automated `dev-scripts.include` gate is prepared; record its source commit and host/tool evidence here after the first successful run, then delete this item.
- [ ] Tag v0.1 only after clean-clone reproduction succeeds.

## 18. Deferred work

Do not implement before v0.1 proves the semantic bridge: bundle/public registry publishing, automatic `.sdd` editing or approval, CI integration, rich requirement-to-code traceability, graph/IDE visualization, automatic task rewriting, persistent integration databases, cross-repository authority, or a general bridge-policy language.

## 19. Next coding session

Review the automated clean-clone acceptance output.

If it reports `clean-clone acceptance: PASS`:

- record the exercised commit and exact host/tool versions in the current baseline;
- delete the completed clean-clone TODO item;
- confirm generated and ignored state remained outside canonical source;
- proceed to the v0.1 tagging decision.

If it fails, fix canonical source rather than generated Spec Kit state, rerun the clean-clone gate, and do not tag v0.1.

## 20. Definition of done for v0.1

- [ ] Spec Kit core remains unmodified.
- [ ] SpecDD core remains unmodified.
- [ ] A clean clone reproduces the documented development setup and acceptance checks.

## 21. Core implementation constraint

Spec Kit owns the change lifecycle. SpecDD owns persistent system semantics. The bridge resolves, projects, validates, and verifies; it must not become a third competing specification system.
