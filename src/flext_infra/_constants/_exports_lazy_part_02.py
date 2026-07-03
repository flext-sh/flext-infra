# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".base": ("s",),
        ".fixers.base": ("FlextInfraFixerAdapter",),
        ".fixers.gate_fixer": ("FlextInfraGateFixerAdapter",),
        ".fixers.orchestrator": ("FlextInfraEnforcementFixerOrchestrator",),
        ".fixers.result": ("FlextInfraFixersResult",),
        ".fixers.transformer_fixer": ("FlextInfraTransformerFixerAdapter",),
        ".transformers": ("transformers",),
        ".typings": ("t",),
        ".utilities": ("u",),
        ".validate": ("validate",),
        ".workspace": ("workspace",),
        "flext_core": (
            "d",
            "e",
            "h",
            "r",
            "x",
        ),
    },
)

__all__: list[str] = ["FLEXT_INFRA_LAZY_IMPORTS_PART_02"]
