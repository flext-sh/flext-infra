"""Tests package for flext-infra."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_flext_core_path = Path(__file__).parent.parent.parent / "flext-core"
if str(_flext_core_path) not in sys.path:
    sys.path.insert(0, str(_flext_core_path))

_tests_models = importlib.import_module("tests.models")
TestsFlextModels = _tests_models.TestsFlextModels

__all__ = ["TestsFlextModels"]
