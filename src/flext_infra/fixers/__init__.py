# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.fixers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextInfraFixerAdapter
    from .gate_fixer import FlextInfraGateFixerAdapter
    from .manual_fixer import FlextInfraManualFixerAdapter
    from .orchestrator import FlextInfraEnforcementFixerOrchestrator
    from .rope_fixer import FlextInfraRopeFixerAdapter
    from .transformer_fixer import FlextInfraTransformerFixerAdapter
__all__: tuple[str, ...] = (
    "FlextInfraEnforcementFixerOrchestrator",
    "FlextInfraFixerAdapter",
    "FlextInfraGateFixerAdapter",
    "FlextInfraManualFixerAdapter",
    "FlextInfraRopeFixerAdapter",
    "FlextInfraTransformerFixerAdapter",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".base": ("FlextInfraFixerAdapter",),
            ".gate_fixer": ("FlextInfraGateFixerAdapter",),
            ".manual_fixer": ("FlextInfraManualFixerAdapter",),
            ".orchestrator": ("FlextInfraEnforcementFixerOrchestrator",),
            ".rope_fixer": ("FlextInfraRopeFixerAdapter",),
            ".transformer_fixer": ("FlextInfraTransformerFixerAdapter",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
