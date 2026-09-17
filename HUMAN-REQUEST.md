# Human Request — Create v0.1 Release Tag

The current accepted v0.1 release commit is:

    78834d9105b70d2b4a5a36ac8885765649a2d963

The supplied clean-clone acceptance evidence passed at that exact commit, including bootstrap, check mode, all 88 tests, fixture lint, patch-integrity checks, canonical-source cleanliness, and tracked-file ignore-policy validation.

Creating a Git tag changes repository refs rather than working-tree files, so perform the remaining release action from the repository root:

    git rev-parse 78834d9105b70d2b4a5a36ac8885765649a2d963
    git tag v0.1 78834d9105b70d2b4a5a36ac8885765649a2d963
    git rev-list -n 1 v0.1

The final command must print:

    78834d9105b70d2b4a5a36ac8885765649a2d963

If `v0.1` already exists, do not move or overwrite it. Instead inspect it with:

    git rev-list -n 1 v0.1

and report the existing target.

After the tag is confirmed at the accepted commit, the next iteration should remove the remaining Phase 15 task from `docs/TODO.md` and delete this file.

---------

Response:

```
[22:05] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ git rev-parse 78834d9105b70d2b4a5a36ac8885765649a2d963
78834d9105b70d2b4a5a36ac8885765649a2d963

[22:06] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ git tag v0.1 78834d9105b70d2b4a5a36ac8885765649a2d963

[22:06] Domas@h87m-g43-win10 MINGW64 ~/projektai/speckit-specdd (main)
$ git rev-list -n 1 v0.1
78834d9105b70d2b4a5a36ac8885765649a2d963
```