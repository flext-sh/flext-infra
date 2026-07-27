"""Tests for the explicit flext_infra.basemk package surface."""

from __future__ import annotations

import pytest
from flext_tests import tm

import flext_infra.basemk as basemk_module
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer


class TestsFlextInfraBasemkInit:
    """Tests for flext_infra.basemk module."""

    def test_unknown_symbol_raises_attribute_error(self) -> None:
        """Reject symbols outside the explicit package surface."""
        with pytest.raises(AttributeError):
            _ = getattr(basemk_module, "nonexistent_symbol_xyz")

    def test_submodule_import_exposes_template_renderer(self) -> None:
        """Import the renderer explicitly from its owning submodule."""
        tm.that(FlextInfraBaseMkTemplateRenderer, none=False)

    def test_submodule_import_exposes_generator(self) -> None:
        """Import the generator explicitly from its owning submodule."""
        tm.that(FlextInfraBaseMkGenerator, none=False)

    def test_root_package_has_no_flat_service_aliases(self) -> None:
        """Keep services owned by their explicit submodules."""
        exports = dir(basemk_module)
        tm.that(basemk_module.__all__, eq=())
        tm.that(exports, lacks="FlextInfraBaseMkTemplateRenderer")
        tm.that(exports, lacks="FlextInfraBaseMkGenerator")
