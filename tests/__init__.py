"""Tests package for flext-infra."""

from __future__ import annotations

import sys
from pathlib import Path

_flext_core_path = Path(__file__).resolve().parent.parent.parent / "flext-core"
if str(_flext_core_path) not in sys.path:
    sys.path.insert(0, str(_flext_core_path))

if "tests" in sys.modules:
    del sys.modules["tests"]
if "tests.models" in sys.modules:
    del sys.modules["tests.models"]

from tests.models import TestsFlextModels

__all__ = ["TestsFlextModels"]
