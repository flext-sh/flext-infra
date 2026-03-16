"""Tests package for flext-infra."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_flext_core_tests = (
    Path(__file__).parent.parent.parent / "flext-core" / "tests" / "__init__.py"
)
_spec = importlib.util.spec_from_file_location("_flext_core_tests", _flext_core_tests)
if _spec and _spec.loader:
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    TestsFlextModels = _module.TestsFlextModels
else:
    raise ImportError("Could not load flext-core tests module")

__all__ = ["TestsFlextModels"]
