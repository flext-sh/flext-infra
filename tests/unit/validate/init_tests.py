"""Tests for flext_infra.validate module initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

import flext_infra.validate as core_module
from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator

if TYPE_CHECKING:
    from tests import t


class TestCoreModuleInit:
    """Test core module lazy loading and exports."""

    def test_core_getattr_raises_attribute_error(self) -> None:
        """Test that accessing nonexistent attribute raises AttributeError."""
        with pytest.raises(AttributeError):
            _ = getattr(core_module, "nonexistent_xyz_attribute")

    def test_validate_package_does_not_reexport_leaf_implementations(self) -> None:
        """Keep validator implementations available only from leaf owners."""
        exports = dir(core_module)
        tm.that(core_module.__all__, eq=())
        for implementation in (
            "FlextInfraBaseMkValidator",
            "FlextInfraInventoryService",
            "FlextInfraSkillValidator",
            "FlextInfraStubSupplyChain",
            "FlextInfraTextPatternScanner",
        ):
            tm.that(exports, lacks=implementation)

    def test_core_lazy_imports_work(self) -> None:
        """Test that lazy imports resolve to real classes."""
        tm.that(FlextInfraBaseMkValidator, none=False)


__all__: t.StrSequence = []
