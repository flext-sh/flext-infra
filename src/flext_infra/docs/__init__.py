# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.docs.auditor import FlextInfraDocAuditor
    from flext_infra.docs.auditor_mixin import FlextInfraDocAuditorMixin
    from flext_infra.docs.base import FlextInfraDocServiceBase
    from flext_infra.docs.builder import FlextInfraDocBuilder
    from flext_infra.docs.fixer import FlextInfraDocFixer
    from flext_infra.docs.generator import FlextInfraDocGenerator
    from flext_infra.docs.validator import FlextInfraDocValidator
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


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
