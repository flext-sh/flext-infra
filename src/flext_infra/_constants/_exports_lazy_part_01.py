# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_LAZY_IMPORTS_PART_01 = build_lazy_import_map(
    {
        "._constants": ("_constants",),
        "._enforcement": ("_enforcement",),
        "._enforcement.collection_base": (
            "FlextInfraEnforcementCollectionBase",
            "FlextInfraEnforcementEvaluation",
        ),
        "._enforcement.collection_sources": ("FlextInfraEnforcementSourceCollectors",),
        "._enforcement.collection_tests": ("FlextInfraEnforcementTestsCollector",),
        "._enforcement.engine": ("FlextInfraEnforcementEngine",),
        "._enforcement.metadata": ("FlextInfraEnforcementMetadata",),
        "._enforcement.selection": ("FlextInfraEnforcementSelection",),
        "._fixtures.enforcement": ("FlextInfraEnforcementPytestPlugin",),
        "._models": ("_models",),
        "._protocols": ("_protocols",),
        "._typings": ("_typings",),
        "._utilities": ("_utilities",),
        ".api": ("FlextInfra",),
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
        ".models": ("FlextInfraModels",),
        ".protocols": ("FlextInfraProtocols",),
        ".settings": ("FlextInfraSettings",),
        ".typings": ("FlextInfraTypes",),
        ".utilities": ("FlextInfraUtilities",),
        "flext_core._root_typing_parts.facades": ("d",),
    },
)

__all__: list[str] = ["FLEXT_INFRA_LAZY_IMPORTS_PART_01"]
