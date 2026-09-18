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
    operation_authority=None,
    invalid_operation_authorities=(),
):
    return validation.TaskRecord(
        order=0,
        task_id=task_id,
        story=story,
        text="fixture task",
        targets=tuple(targets),
        spec_targets=tuple(spec_targets),
        invalid_targets=tuple(invalid_targets),
        operation_authority=operation_authority,
        invalid_operation_authorities=tuple(invalid_operation_authorities),
    )


def permitted_cross_owned_task():
    auth = "src/auth/auth.sdd"
    users = "src/users/users.sdd"
    users_path = "src/users/repository.ts"
    return {
        0: {
            users_path: {
                "owner": users,
                "allowedAuthorities": [users, auth],
                "canModifySources": {auth: [auth]},
            },
        }
    }
