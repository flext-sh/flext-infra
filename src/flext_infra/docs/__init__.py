# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCliDocs": ".cli",
    "FlextInfraDocAuditor": ".auditor",
    "FlextInfraDocAuditorMixin": "._auditor_mixin",
    "FlextInfraDocBuilder": ".builder",
    "FlextInfraDocFixer": ".fixer",
    "FlextInfraDocGenerator": ".generator",
    "FlextInfraDocValidator": ".validator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
