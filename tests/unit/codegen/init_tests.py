"""Tests for flext_infra.codegen module initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

import flext_infra.codegen as codegen_module
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_tests import tm

# Why: the symbol must be absent for the test to mean anything, so it
# cannot be spelled as a static attribute access without making the file
# ill-typed. The name is data here, and getattr is the access it tests.
_ABSENT_SYMBOL = "nonexistent_xyz_attribute"


def test_codegen_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(codegen_module, _ABSENT_SYMBOL)


def test_codegen_package_does_not_reexport_leaf_implementations() -> None:
    """Keep implementation classes available only from their leaf owners."""
    exports = dir(codegen_module)
    tm.that(codegen_module.__all__, eq=())
    tm.that(exports, lacks="FlextInfraCodegenLazyInit")


def test_codegen_lazy_imports_work() -> None:
    """Test that lazy imports work correctly."""
    tm.that(type(FlextInfraCodegenLazyInit).__name__, eq="ModelMetaclass")


__all__: list[str] = []
