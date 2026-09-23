from boundary_test_support import validation


def sample_boundary():
    return {
        "schemaVersion": 1,
        "feature": "001-login",
        "targets": [
            {
                "path": "src/auth/service.ts",
                "primaryAuthority": "src/auth/auth.sdd",
                "resolvedSpecs": ["project.sdd", "src/auth/auth.sdd"],
            },
            {
                "path": "src/users/repository.ts",
                "primaryAuthority": "src/users/users.sdd",
                "resolvedSpecs": ["project.sdd", "src/users/users.sdd"],
            },
        ],
        "authorities": ["src/auth/auth.sdd", "src/users/users.sdd"],
        "crossBoundary": True,
        "unresolved": [],
        "generation": {
            "specddCliVersion": "1.1.1",
            "specddFrameworkVersion": "1.5",
        },
    }


def task(
    *,
    task_id="T001",
    story="US1",
    targets=(),
    spec_targets=(),
    invalid_targets=(),
    writes_declared=True,
    write_metadata_errors=(),
):
    return validation.TaskRecord(
        order=0,
        task_id=task_id,
        story=story,
        text="fixture task",
        targets=tuple(targets),
        spec_targets=tuple(spec_targets),
        invalid_targets=tuple(invalid_targets),
        writes_declared=writes_declared,
        write_metadata_errors=tuple(write_metadata_errors),
    )
