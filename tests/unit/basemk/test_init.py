"""Tests for flext_infra.basemk module initialization.

Tests lazy loading and __getattr__ fallthrough behavior.
"""

from __future__ import annotations

import pytest

import flext_infra.basemk as basemk_module
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm


class TestsFlextInfraBasemkInit:
    """Tests for flext_infra.basemk module."""

    def test_getattr_raises_attribute_error_for_unknown_symbol(self) -> None:
        """Test __getattr__ raises AttributeError for unknown attributes."""
        with pytest.raises(AttributeError):
            _ = getattr(basemk_module, "nonexistent_symbol_xyz")

    def test_lazy_import_template_renderer(self) -> None:
        """Test lazy import of FlextInfraBaseMkTemplateRenderer."""
        tm.that(FlextInfraBaseMkTemplateRenderer, none=False)

    def test_lazy_import_generator(self) -> None:
        """Test lazy import of FlextInfraBaseMkGenerator."""
        tm.that(FlextInfraBaseMkGenerator, none=False)

    def test_dir_returns_all_exports(self) -> None:
        """Test dir() returns all exported symbols."""
        exports = dir(basemk_module)
        tm.that(exports, has="FlextInfraBaseMkTemplateRenderer")
        tm.that(exports, has="FlextInfraBaseMkGenerator")
