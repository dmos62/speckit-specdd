# Human Request: Change Boundary schema write authority

The first unresolved P1 task in `docs/TODO.md` requires changing:

    integration/specdd/schemas/change-boundary.schema.json

SpecDD bootstrap rules require every non-`.sdd` project artifact change to have an authoritative owning spec and pre-operation `Owns` or `Can modify` authority.

The provided effective project context contains references to this schema, but no applicable spec owns it or grants modification permission:

- `integration/specdd/scripts/scripts.sdd` references the schema but does not own or `Can modify` it.
- `tests/tests.sdd` references the schema but does not own or `Can modify` it.
- `speckit-specdd.sdd` does not grant path authority over the schema.

The P1 implementation therefore cannot safely change the schema yet.

Please either:

1. identify the existing authoritative spec that owns `integration/specdd/schemas/change-boundary.schema.json`; or
2. explicitly authorize, in the same operation, creating/updating a suitable schema spec (for example `integration/specdd/schemas/change-boundary.sdd` owning `./change-boundary.schema.json`) and making the corresponding schema change.

Once that authority is explicit, the intended P1 change is to make `INTENDED_TARGET_UNSUPPORTED` a schema-valid machine-readable unresolved code, remove reliance on that token appearing in diagnostic message text, update focused projection/validation tests, and remove the completed TODO item.

-------

Response: alter the sdd files as appropriate.
