# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .auditor import FlextInfraDocAuditor
    from .auditor_mixin import FlextInfraDocAuditorMixin
    from .base import FlextInfraDocServiceBase
    from .builder import FlextInfraDocBuilder
    from .fixer import FlextInfraDocFixer
    from .generator import FlextInfraDocGenerator
    from .server import FlextInfraDocServer
    from .validator import FlextInfraDocValidator

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".auditor": ("FlextInfraDocAuditor",),
    ".auditor_mixin": ("FlextInfraDocAuditorMixin",),
    ".base": ("FlextInfraDocServiceBase",),
    ".builder": ("FlextInfraDocBuilder",),
    ".fixer": ("FlextInfraDocFixer",),
    ".generator": ("FlextInfraDocGenerator",),
    ".server": ("FlextInfraDocServer",),
    ".validator": ("FlextInfraDocValidator",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraDocAuditor",
    "FlextInfraDocAuditorMixin",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocServer",
    "FlextInfraDocServiceBase",
    "FlextInfraDocValidator",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
