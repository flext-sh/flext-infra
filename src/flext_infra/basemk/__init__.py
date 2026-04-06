# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.basemk.cli as _flext_infra_basemk_cli

    cli = _flext_infra_basemk_cli
    import flext_infra.basemk.engine as _flext_infra_basemk_engine
    from flext_infra.basemk.cli import FlextInfraCliBasemk

    engine = _flext_infra_basemk_engine
    import flext_infra.basemk.generator as _flext_infra_basemk_generator
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine

    generator = _flext_infra_basemk_generator
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
_LAZY_IMPORTS = {
    "FlextInfraBaseMkGenerator": "flext_infra.basemk.generator",
    "FlextInfraBaseMkTemplateEngine": "flext_infra.basemk.engine",
    "FlextInfraCliBasemk": "flext_infra.basemk.cli",
    "cli": "flext_infra.basemk.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "engine": "flext_infra.basemk.engine",
    "generator": "flext_infra.basemk.generator",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
    "FlextInfraCliBasemk",
    "cli",
    "d",
    "e",
    "engine",
    "generator",
    "h",
    "r",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
