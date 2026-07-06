# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_03 = build_lazy_import_map(
    {
        "._constants": ("_constants",),
        ".rope_mro_transform": ("FlextInfraUtilitiesRopeMroTransform",),
        ".rope_pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
        ".rope_runtime": ("FlextInfraUtilitiesRopeRuntime",),
        ".rope_runtime_base": ("FlextInfraUtilitiesRopeRuntimeBase",),
        ".rope_runtime_modules": ("FlextInfraUtilitiesRopeRuntimeModules",),
        ".rope_runtime_refactors": ("FlextInfraUtilitiesRopeRuntimeRefactors",),
        ".rope_runtime_types": ("FlextInfraUtilitiesRopeRuntimeTypes",),
        ".rope_source": ("FlextInfraUtilitiesRopeSource",),
        ".safety": ("FlextInfraUtilitiesSafety",),
        ".silent_failure_ast": (
            "collect_silent_failure_findings",
            "collect_silent_failure_fixes",
        ),
        ".snapshot": ("FlextInfraUtilitiesSnapshot",),
        ".versioning": ("FlextInfraUtilitiesVersioning",),
    },
)

__all__: list[str] = ["FLEXT_INFRA__UTILITIES_LAZY_IMPORTS_PART_03"]
