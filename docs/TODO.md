# Spec Kit × SpecDD Integration Implementation Plan

Status: Release-ready
Target: v0.1

Completed phases are removed from this file; remaining phase numbers stay stable so references to the original implementation plan do not drift.

## 1. Current baseline

The v0.1 semantic bridge is implemented and its release acceptance gate has passed.

The latest clean-clone acceptance succeeded from committed source:

    78834d9105b70d2b4a5a36ac8885765649a2d963

This supersedes the previously recorded accepted commit. The exercised host and tool evidence remains:

- Windows 10 `10.0.19045` on AMD64.
- Node.js `v22.14.0`.
- Python `3.12.11`.
- Spec Kit `1.0.7`.
- SpecDD CLI `1.1.1`.
- SpecDD framework `1.5`.

The clean clone successfully completed:

- repository bootstrap;
- bootstrap check mode;
- all 88 tests;
- real two-domain fixture lint;
- `git diff --check`;
- canonical-source cleanliness validation;
- tracked-file ignore-policy validation.

Supported development-mode installation rematerialized generated state under `.agents/skills/` and `.specify/`, including extension and preset registry state and the installed workflow overlay. Those changes remained outside canonical bridge source, and no unexpected canonical-source changes were present.

Compatibility remains pinned to Node.js 22+, Spec Kit `1.0.7`, SpecDD CLI `1.1.1`, and SpecDD framework `1.5`. Other operating systems, Python versions, and adjacent Spec Kit or SpecDD versions remain unverified until exercised directly.

The remaining v0.1 action is to create the `v0.1` tag at the accepted commit above. This is a repository-ref operation rather than a working-tree file change.

## 15. Phase 15 — v0.1 hardening

### TODO

- [ ] Tag `v0.1` at accepted release commit `78834d9105b70d2b4a5a36ac8885765649a2d963`.

## 18. Deferred work

Do not implement before v0.1 proves the semantic bridge: bundle/public registry publishing, automatic `.sdd` editing or approval, CI integration, rich requirement-to-code traceability, graph/IDE visualization, automatic task rewriting, persistent integration databases, cross-repository authority, or a general bridge-policy language.

## 19. Next coding session

The clean-clone release gate is complete for `78834d9105b70d2b4a5a36ac8885765649a2d963`.

Create the `v0.1` tag at that exact commit. Do not move the tag to later bookkeeping-only changes.

After the tag is confirmed, delete the remaining Phase 15 task. With no remaining implementation work, this TODO should then be empty.

## 21. Core implementation constraint

Spec Kit owns the change lifecycle. SpecDD owns persistent system semantics. The bridge resolves, projects, validates, and verifies; it must not become a third competing specification system.
