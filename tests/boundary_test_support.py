import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "integration"
    / "specdd"
    / "scripts"
    / "boundary.py"
)
VALIDATION_SCRIPT_PATH = (
    REPO_ROOT
    / "integration"
    / "specdd"
    / "scripts"
    / "validation.py"
)
VERIFICATION_SCRIPT_PATH = (
    REPO_ROOT
    / "integration"
    / "specdd"
    / "scripts"
    / "verification.py"
)
WORKFLOW_GATE_SCRIPT_PATH = (
    REPO_ROOT
    / "integration"
    / "specdd"
    / "scripts"
    / "workflow_gate.py"
)
FIXTURE_ROOT = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "specdd-two-domain"
)


def _load_module(
    name,
    path,
):
    module_spec = importlib.util.spec_from_file_location(
        name,
        path,
    )
    module = importlib.util.module_from_spec(
        module_spec
    )
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def resolver_payload(specs):
    return json.dumps(
        {"directories": [{"path": "/", "specs": specs}]}
    )


boundary = _load_module(
    "specdd_boundary",
    SCRIPT_PATH,
)
validation = _load_module(
    "specdd_validation",
    VALIDATION_SCRIPT_PATH,
)
verification = _load_module(
    "specdd_verification",
    VERIFICATION_SCRIPT_PATH,
)
workflow_gate = _load_module(
    "specdd_workflow_gate",
    WORKFLOW_GATE_SCRIPT_PATH,
)
