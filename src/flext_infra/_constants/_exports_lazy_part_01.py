# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_LAZY_IMPORTS_PART_01 = build_lazy_import_map(
    {
        "._constants": ("_constants",),
        "._models": ("_models",),
        "._protocols": ("_protocols",),
        "._typings": ("_typings",),
        "._utilities": ("_utilities",),
        ".api": (
            "FlextInfra",
            "infra",
        ),
        ".base": ("FlextInfraServiceBase",),
        ".base_selection": ("FlextInfraProjectSelectionServiceBase",),
        ".basemk": ("basemk",),
        ".check": ("check",),
        ".cli": ("FlextInfraCli",),
        ".codegen": ("codegen",),
        ".constants": (
            "FlextInfraConstants",
            "c",
        ),
        ".deps": ("deps",),
        ".detectors": ("detectors",),
        ".docs": ("docs",),
        ".fixers": ("fixers",),
        ".fixers.base": ("FlextInfraFixerAdapter",),
        ".fixers.gate_fixer": ("FlextInfraGateFixerAdapter",),
        ".fixers.orchestrator": ("FlextInfraEnforcementFixerOrchestrator",),
        ".fixers.result": ("FlextInfraFixersResult",),
        ".fixers.transformer_fixer": ("FlextInfraTransformerFixerAdapter",),
        ".gates": ("gates",),
        ".models": (
            "FlextInfraModels",
            "m",
        ),
        ".protocols": (
            "FlextInfraProtocols",
            "FlextInfraProtocolsBase",
        ),
        ".settings": ("FlextInfraSettings",),
        ".typings": ("FlextInfraTypes",),
        ".utilities": ("FlextInfraUtilities",),
    },
)

__all__: list[str] = ["FLEXT_INFRA_LAZY_IMPORTS_PART_01"]
