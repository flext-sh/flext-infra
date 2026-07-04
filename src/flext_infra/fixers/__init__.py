# AUTO-GENERATED FILE — Regenerate with: make gen
"""Fixers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

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
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraFixerAdapter",),
        ".gate_fixer": ("FlextInfraGateFixerAdapter",),
        ".manual_fixer": ("FlextInfraManualFixerAdapter",),
        ".orchestrator": ("FlextInfraEnforcementFixerOrchestrator",),
        ".result": ("FlextInfraFixersResult",),
        ".rope_fixer": ("FlextInfraRopeFixerAdapter",),
        ".transformer_fixer": ("FlextInfraTransformerFixerAdapter",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
