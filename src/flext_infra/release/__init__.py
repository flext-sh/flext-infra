# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCliRelease": ("flext_infra.release.cli", "FlextInfraCliRelease"),
    "FlextInfraReleaseOrchestrator": (
        "flext_infra.release.orchestrator",
        "FlextInfraReleaseOrchestrator",
    ),
    "FlextInfraReleaseOrchestratorPhases": (
        "flext_infra.release.orchestrator_phases",
        "FlextInfraReleaseOrchestratorPhases",
    ),
    "cli": "flext_infra.release.cli",
    "orchestrator": "flext_infra.release.orchestrator",
    "orchestrator_phases": "flext_infra.release.orchestrator_phases",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
