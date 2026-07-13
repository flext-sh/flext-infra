# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.transformers.smells package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.transformers.smells.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.transformers.smells.base import (
        FlextInfraSmellFixer as FlextInfraSmellFixer,
        auto_fixable_smell_tags as auto_fixable_smell_tags,
        register_smell_fixer as register_smell_fixer,
        smell_fixer_for as smell_fixer_for,
    )
    from flext_infra.transformers.smells.boolean_logic import (
        FlextInfraBooleanLogicFixer as FlextInfraBooleanLogicFixer,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
