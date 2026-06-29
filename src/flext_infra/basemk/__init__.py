# AUTO-GENERATED FILE — Regenerate with: make gen
"""Basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.basemk.engine import (
        FlextInfraBaseMkTemplateEngine as FlextInfraBaseMkTemplateEngine,
    )
    from flext_infra.basemk.generator import (
        FlextInfraBaseMkGenerator as FlextInfraBaseMkGenerator,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".engine": ("FlextInfraBaseMkTemplateEngine",),
        ".generator": ("FlextInfraBaseMkGenerator",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
