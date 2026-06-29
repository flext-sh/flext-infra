# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".auditor": ("FlextInfraDocAuditor",),
        ".auditor_mixin": ("FlextInfraDocAuditorMixin",),
        ".base": ("FlextInfraDocServiceBase",),
        ".builder": ("FlextInfraDocBuilder",),
        ".fixer": ("FlextInfraDocFixer",),
        ".generator": ("FlextInfraDocGenerator",),
        ".validator": ("FlextInfraDocValidator",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
