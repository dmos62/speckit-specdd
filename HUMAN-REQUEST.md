# Human request

The current iteration is blocked before a safe code edit can be produced.

The reported regression is localized: `tests/test_boundary.py::BoundaryOutputTests.test_missing_target_is_preserved_as_unresolved` reaches `build_change_boundary()`, but the generated `unresolved[0]` object lacks the schema-required `code` property. The likely fix is to make the missing-target diagnostic use the same structured unresolved-diagnostic construction as the adapter's other failure cases.

The repository worktree itself is not available to this agent, and the prompt does not include the current contents of the files needed to make that edit safely. SpecDD also requires the applicable owning spec and modification authority to be resolved before changing non-`.sdd` artifacts.

Please make the worktree available to the next programming iteration, or provide the following current files together with the applicable project `.sdd` specs:

    integration/specdd/scripts/boundary.py
    integration/specdd/schemas/change-boundary.schema.json
    tests/test_boundary.py
    tests/test_change_boundary_schema.py
    speckit-specdd.sdd
    any directory-level or same-basename .sdd specs governing those paths

If collecting them manually, the following bash commands provide the necessary context:

    find . -name '*.sdd' -print | sort
    cat speckit-specdd.sdd 2>/dev/null || true
    cat integration/specdd/scripts/boundary.py
    cat integration/specdd/schemas/change-boundary.schema.json
    cat tests/test_boundary.py
    cat tests/test_change_boundary_schema.py

Do not change the schema merely to hide the failure unless its contract shows that `code` is intentionally optional. The current evidence instead points to the adapter omitting a required diagnostic field for the missing-target branch.
