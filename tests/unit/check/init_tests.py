"""Tests for flext_infra.check module initialization.

Tests lazy loading and __getattr__ fallthrough behavior.
"""

from __future__ import annotations

import pytest

import flext_infra.check as check_module
from flext_tests import tm


class TestFlextInfraCheck:
    """Tests for flext_infra.check module."""

    def test_getattr_raises_attribute_error_for_unknown_symbol(self) -> None:
        """Test __getattr__ raises AttributeError for unknown attributes."""
        with pytest.raises(AttributeError):
            _ = getattr(check_module, "nonexistent_symbol_xyz")

    def test_dir_exposes_no_leaf_exports(self) -> None:
        """Keep leaf implementations out of the package-level public surface."""
        exports = dir(check_module)
        tm.that(exports, is_=list)
        tm.that(exports, empty=True)
