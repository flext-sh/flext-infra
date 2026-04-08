# AUTO-GENERATED FILE — Regenerate with: make gen
"""Basemk package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraBaseMkGenerator": ".generator",
    "FlextInfraBaseMkTemplateEngine": ".engine",
    "FlextInfraCliBasemk": ".cli",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
