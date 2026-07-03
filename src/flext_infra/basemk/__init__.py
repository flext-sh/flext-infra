# AUTO-GENERATED FILE — Regenerate with: make gen
"""Basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.basemk.generator import (
        FlextInfraBaseMkGenerator as FlextInfraBaseMkGenerator,
    )
    from flext_infra.basemk.renderer import (
        FlextInfraBaseMkTemplateRenderer as FlextInfraBaseMkTemplateRenderer,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".generator": ("FlextInfraBaseMkGenerator",),
        ".renderer": ("FlextInfraBaseMkTemplateRenderer",),
    },
)
    from flext_core.typings import FlextTypes
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "FlextInfraBaseMkGenerator": (
        "flext_infra.basemk.generator",
        "FlextInfraBaseMkGenerator",
    ),
    "FlextInfraBaseMkTemplateEngine": (
        "flext_infra.basemk.engine",
        "FlextInfraBaseMkTemplateEngine",
    ),
}

__all__ = [
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
]


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
