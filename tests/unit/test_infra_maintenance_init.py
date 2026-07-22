"""Tests for flext_infra.maintenance module initialization.

Tests lazy loading and __getattr__ fallthrough behavior.
"""

from __future__ import annotations

import pytest
from flext_tests import tm

import flext_infra.maintenance
from flext_infra.maintenance.python_version import FlextInfraPythonVersionEnforcer


class TestsFlextInfraInfraMaintenanceInit:
    """Tests for flext_infra.maintenance module."""

    def test_getattr_raises_attribute_error_for_unknown_symbol(self) -> None:
        """Test __getattr__ raises AttributeError for unknown attributes."""
        with pytest.raises(AttributeError):
            _ = getattr(flext_infra.maintenance, "nonexistent_symbol_xyz")

    def test_lazy_import_python_version_enforcer(self) -> None:
        """Test lazy import of FlextInfraPythonVersionEnforcer."""
        tm.that(FlextInfraPythonVersionEnforcer, none=False)

    def test_package_does_not_reexport_leaf_implementations(self) -> None:
        """Keep maintenance implementations available only from leaf owners."""
        exports = dir(flext_infra.maintenance)
        tm.that(flext_infra.maintenance.__all__, eq=())
        tm.that(exports, lacks="FlextInfraPythonVersionEnforcer")
