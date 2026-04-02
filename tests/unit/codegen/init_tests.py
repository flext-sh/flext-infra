"""Tests for flext_infra.codegen module initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

import flext_infra.codegen as codegen_module
from flext_infra import FlextInfraCodegenLazyInit
from tests import t


def test_codegen_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(codegen_module, "nonexistent_xyz_attribute")


def test_codegen_dir_returns_all_exports() -> None:
    """Test that dir() returns all exported attributes."""
    exports = dir(codegen_module)
    tm.that(exports, has="FlextInfraCodegenLazyInit")


def test_codegen_lazy_imports_work() -> None:
    """Test that lazy imports work correctly."""
    tm.that(type(FlextInfraCodegenLazyInit).__name__, eq="ModelMetaclass")
    tm.that(hasattr(FlextInfraCodegenLazyInit, "run"), eq=True)


__all__: t.StrSequence = []
