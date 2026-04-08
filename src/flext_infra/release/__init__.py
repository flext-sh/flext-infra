# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCliRelease": ".cli",
    "FlextInfraReleaseOrchestrator": ".orchestrator",
    "FlextInfraReleaseOrchestratorPhases": ".orchestrator_phases",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
