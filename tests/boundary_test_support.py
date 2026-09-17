import importlib.util
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


boundary = _load_module(
    "specdd_boundary",
    SCRIPT_PATH,
)
validation = _load_module(
    "specdd_validation",
    VALIDATION_SCRIPT_PATH,
)
