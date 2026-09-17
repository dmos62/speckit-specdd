# Human Request: Authorize the root README

Phase 14 requires creating the repository-root `README.md`.

The current SpecDD authority snapshot does not identify `README.md` in an `Owns` or `Can modify` entry. The bootstrap contract requires explicit modification permission before creating a non-`.sdd` project artifact, so the README has not been created.

To complete the README in one subsequent operation, explicitly authorize both parts of the authority change, for example:

    Add ./README.md to the root speckit-specdd.sdd ownership and create README.md in the same operation.

Without that same-operation authorization, the safe sequence is to add `./README.md` to the root spec first, end that operation, and create the README only after a fresh authority snapshot.

No generated Spec Kit or SpecDD state needs to be edited for this decision.
