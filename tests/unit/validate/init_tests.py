"""Tests for flext_infra.validate module initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

import flext_infra.validate as core_module
from flext_infra import FlextInfraBaseMkValidator, t


class TestCoreModuleInit:
    """Test core module lazy loading and exports."""

    def test_core_getattr_raises_attribute_error(self) -> None:
        """Test that accessing nonexistent attribute raises AttributeError."""
        with pytest.raises(AttributeError):
            _ = getattr(core_module, "nonexistent_xyz_attribute")

    def test_core_dir_returns_all_exports(self) -> None:
        """Test that dir() returns all exported attributes."""
        exports = dir(core_module)
        tm.that(exports, has="FlextInfraBaseMkValidator")
        tm.that(exports, has="FlextInfraInventoryService")
        tm.that(exports, has="FlextInfraSkillValidator")
        tm.that(exports, has="FlextInfraStubSupplyChain")
        tm.that(exports, has="FlextInfraTextPatternScanner")

    def test_core_lazy_imports_work(self) -> None:
        """Test that lazy imports resolve to real classes."""
        tm.that(FlextInfraBaseMkValidator, none=False)
        tm.that(hasattr(FlextInfraBaseMkValidator, "validate"), eq=True)


__all__: t.StrSequence = []
