"""Tests for release module __init__.py lazy imports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

import flext_infra.release as release_module
from flext_infra import FlextInfraReleaseOrchestrator


class TestReleaseInit:
    """Test release module __init__.py lazy imports."""

    def test_lazy_import_orchestrator(self) -> None:
        orchestrator = release_module.FlextInfraReleaseOrchestrator()
        tm.that(orchestrator, is_=FlextInfraReleaseOrchestrator)

    def test_getattr_invalid_attribute(self) -> None:
        with pytest.raises(AttributeError, match=r"module.*has no attribute"):
            _ = getattr(release_module, "NonexistentAttribute")

    def test_dir_returns_all_exports(self) -> None:
        exports = dir(release_module)
        tm.that(exports, has="FlextInfraReleaseOrchestrator")
