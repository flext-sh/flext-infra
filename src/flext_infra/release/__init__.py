# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.release package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .orchestrator import FlextInfraReleaseOrchestrator
    from .orchestrator_phases import FlextInfraReleaseOrchestratorPhases
__all__: tuple[str, ...] = (
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseOrchestratorPhases",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".orchestrator": ("FlextInfraReleaseOrchestrator",),
                ".orchestrator_phases": ("FlextInfraReleaseOrchestratorPhases",),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
