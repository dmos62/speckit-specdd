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
FIXTURE_ROOT = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "specdd-two-domain"
)

module_spec = importlib.util.spec_from_file_location(
    "specdd_boundary",
    SCRIPT_PATH,
)
boundary = importlib.util.module_from_spec(
    module_spec
)
sys.modules[module_spec.name] = boundary
module_spec.loader.exec_module(boundary)
