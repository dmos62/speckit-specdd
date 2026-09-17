# Human request

The current regression is understood, but the code edit is blocked by SpecDD write authority.

The failing test is:

    tests/test_boundary.py::BoundaryOutputTests.test_missing_target_is_preserved_as_unresolved

The checked-in Change Boundary schema requires every unresolved target to contain:

- `input`
- `code`
- `message`

The adapter currently models unresolved diagnostics as only `input`, `reason`, and optional `path`, and `_unresolved_record()` maps those fields dynamically from the schema. As a result, the missing-target branch reaches schema validation without the required `code` property.

The likely implementation direction is to make unresolved diagnostics explicitly structured, including a diagnostic code such as `UNRESOLVED_TARGET`, and serialize the existing schema fields without weakening the schema. Other failure branches should use the appropriate existing schema codes:

- `INVALID_TARGET`
- `UNRESOLVED_TARGET`
- `RESOLUTION_FAILED`
- `AMBIGUOUS_AUTHORITY`

However, the supplied SpecDD authority currently does not permit modifying the relevant non-`.sdd` files. `speckit-specdd.sdd` owns repository-wide bridge architecture conceptually, but its path authority does not cover:

    integration/specdd/scripts/boundary.py
    integration/specdd/schemas/change-boundary.schema.json
    tests/test_boundary.py
    tests/test_change_boundary_schema.py

SpecDD requires non-spec changes to be covered by the pre-operation `Owns` or `Can modify` authority snapshot.

For the next programming iteration, please provide any existing `.sdd` specs that grant modification authority over those paths, or explicitly authorize creating/updating the appropriate governing `.sdd` specs and making the corresponding code/test changes in the same operation.

The following command will show the current spec inventory:

    find . -name '*.sdd' -print | sort

Do not weaken the schema to make the failing test pass. The current schema contract clearly makes `code` required.
