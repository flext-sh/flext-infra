# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra.docs.auditor import FlextInfraDocAuditor as FlextInfraDocAuditor
    from flext_infra.docs.auditor_mixin import (
        FlextInfraDocAuditorMixin as FlextInfraDocAuditorMixin,
    )
    from flext_infra.docs.base import (
        FlextInfraDocServiceBase as FlextInfraDocServiceBase,
    )
    from flext_infra.docs.builder import FlextInfraDocBuilder as FlextInfraDocBuilder
    from flext_infra.docs.fixer import FlextInfraDocFixer as FlextInfraDocFixer
    from flext_infra.docs.generator import (
        FlextInfraDocGenerator as FlextInfraDocGenerator,
    )
    from flext_infra.docs.validator import (
        FlextInfraDocValidator as FlextInfraDocValidator,
    )
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
