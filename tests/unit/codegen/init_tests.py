"""Tests for flext_infra.codegen module initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys

import pytest

import flext_infra.codegen as codegen_module
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_tests import tm


def _loaded_leaf_modules() -> tuple[str, ...]:
    """Implementation leaf modules currently imported (eager-import probe).

    The test module itself imports ``lazy_init`` (the generator), so the probe
    reports only the leaf implementations the package publish path could load.
    """
    return tuple(
        name
        for name in sys.modules
        if name.startswith("flext_infra.codegen.")
        and name != "flext_infra.codegen.lazy_init"
    )


# Why: the symbol must be absent for the test to mean anything, so it
# cannot be spelled as a static attribute access without making the file
# ill-typed. The name is data here, and getattr is the access it tests.
_ABSENT_SYMBOL = "nonexistent_xyz_attribute"


def test_codegen_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(codegen_module, _ABSENT_SYMBOL)


def test_codegen_package_does_not_reexport_leaf_implementations() -> None:
    """Keep implementation classes lazy behind their leaf owners.

    Why (mro-mhf3d lazy-init law): generated package roots publish their
    surface through PEP 562 lazy exports. ``__all__`` and ``dir()`` name the
    public leaf owners, but resolving the surface imports no implementation
    module — the package root never reexports leaf implementations eagerly.
    The generator's own imports are not the package surface, so the probe
    measures the delta across surface resolution.
    """
    before = _loaded_leaf_modules()
    published_all = tuple(codegen_module.__all__)
    published_dir = tuple(dir(codegen_module))
    after_publish = _loaded_leaf_modules()
    tm.that(bool(published_all), eq=True)
    tm.that("FlextInfraCodegenCensus" in published_all, eq=True)
    tm.that("FlextInfraCodegenCensus" in published_dir, eq=True)
    # Publishing the surface imported no implementation module.
    tm.that(after_publish, eq=before)
    # Attribute access resolves lazily to the leaf owner.
    tm.that(
        codegen_module.FlextInfraCodegenConform.__name__, eq="FlextInfraCodegenConform"
    )


def test_codegen_lazy_imports_work() -> None:
    """Test that lazy imports work correctly."""
    tm.that(type(FlextInfraCodegenLazyInit).__name__, eq="ModelMetaclass")


__all__: list[str] = []
