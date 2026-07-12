# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.fixers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.fixers.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.fixers.base import FlextInfraFixerAdapter as FlextInfraFixerAdapter
    from flext_infra.fixers.gate_fixer import (
        FlextInfraGateFixerAdapter as FlextInfraGateFixerAdapter,
    )
    from flext_infra.fixers.manual_fixer import (
        FlextInfraManualFixerAdapter as FlextInfraManualFixerAdapter,
    )
    from flext_infra.fixers.orchestrator import (
        FlextInfraEnforcementFixerOrchestrator as FlextInfraEnforcementFixerOrchestrator,
    )
    from flext_infra.fixers.result import (
        FlextInfraFixersResult as FlextInfraFixersResult,
    )
    from flext_infra.fixers.rope_fixer import (
        FlextInfraRopeFixerAdapter as FlextInfraRopeFixerAdapter,
    )
    from flext_infra.fixers.transformer_fixer import (
        FlextInfraTransformerFixerAdapter as FlextInfraTransformerFixerAdapter,
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
