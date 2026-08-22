"""Tests for flext_infra.check module initialization.

Tests lazy loading and __getattr__ fallthrough behavior.
"""

from __future__ import annotations

import pytest

import flext_infra.check as check_module
from flext_tests import tm

# Why: the symbol must be absent for the test to mean anything, so it
# cannot be spelled as a static attribute access without making the file
# ill-typed. The name is data here, and getattr is the access it tests.
_ABSENT_SYMBOL = "nonexistent_symbol_xyz"


class TestFlextInfraCheck:
    """Tests for flext_infra.check module."""

    def test_getattr_raises_attribute_error_for_unknown_symbol(self) -> None:
        """Test __getattr__ raises AttributeError for unknown attributes."""
        with pytest.raises(AttributeError):
            _ = getattr(check_module, _ABSENT_SYMBOL)

    def test_dir_returns_all_exports(self) -> None:
        """Test dir() returns all exported symbols."""
        exports = dir(check_module)
        tm.that(exports, is_=list)
        tm.that(exports, empty=False)
