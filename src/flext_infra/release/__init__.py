# AUTO-GENERATED FILE — Regenerate with: make gen
"""Release package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.release.orchestrator import (
        FlextInfraReleaseOrchestrator as FlextInfraReleaseOrchestrator,
    )
    from flext_infra.release.orchestrator_phases import (
        FlextInfraReleaseOrchestratorPhases as FlextInfraReleaseOrchestratorPhases,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".orchestrator": ("FlextInfraReleaseOrchestrator",),
        ".orchestrator_phases": ("FlextInfraReleaseOrchestratorPhases",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
