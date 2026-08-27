"""Tests for flext_infra.maintenance module initialization.

Tests lazy loading and __getattr__ fallthrough behavior.
"""

from __future__ import annotations

import flext_infra.maintenance
import pytest
from flext_infra.maintenance.python_version import FlextInfraPythonVersionEnforcer
from flext_tests import tm

# Why: the symbol must be absent for the test to mean anything, so it
# cannot be spelled as a static attribute access without making the file
# ill-typed. The name is data here, and getattr is the access it tests.
_ABSENT_SYMBOL = "nonexistent_symbol_xyz"


class TestsFlextInfraInfraMaintenanceInit:
    """Tests for flext_infra.maintenance module."""

    def test_getattr_raises_attribute_error_for_unknown_symbol(self) -> None:
        """Test __getattr__ raises AttributeError for unknown attributes."""
        with pytest.raises(AttributeError):
            _ = getattr(flext_infra.maintenance, _ABSENT_SYMBOL)

    def test_lazy_import_python_version_enforcer(self) -> None:
        """Test lazy import of FlextInfraPythonVersionEnforcer."""
        tm.that(FlextInfraPythonVersionEnforcer, none=False)

    def test_package_exposes_only_generated_lazy_exports(self) -> None:
        """Keep the package surface equal to the generated lazy export set."""
        tm.that(flext_infra.maintenance.__all__, eq=("FlextInfraCleanService",))
