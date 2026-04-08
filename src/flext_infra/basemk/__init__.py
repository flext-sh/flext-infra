# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraBaseMkGenerator": (
        "flext_infra.basemk.generator",
        "FlextInfraBaseMkGenerator",
    ),
    "FlextInfraBaseMkTemplateEngine": (
        "flext_infra.basemk.engine",
        "FlextInfraBaseMkTemplateEngine",
    ),
    "FlextInfraCliBasemk": ("flext_infra.basemk.cli", "FlextInfraCliBasemk"),
    "cli": "flext_infra.basemk.cli",
    "engine": "flext_infra.basemk.engine",
    "generator": "flext_infra.basemk.generator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
