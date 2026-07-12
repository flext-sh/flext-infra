# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.docs.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
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
    from flext_infra.docs.server import FlextInfraDocServer as FlextInfraDocServer
    from flext_infra.docs.validator import (
        FlextInfraDocValidator as FlextInfraDocValidator,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
