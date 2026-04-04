# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.release._constants as _flext_infra_release__constants

    _constants = _flext_infra_release__constants
    import flext_infra.release._models as _flext_infra_release__models
    from flext_infra.release._constants import FlextInfraReleaseConstants

    _models = _flext_infra_release__models
    import flext_infra.release.cli as _flext_infra_release_cli
    from flext_infra.release._models import FlextInfraReleaseModels

    cli = _flext_infra_release_cli
    import flext_infra.release.orchestrator as _flext_infra_release_orchestrator
    from flext_infra.release.cli import FlextInfraCliRelease

    orchestrator = _flext_infra_release_orchestrator
    import flext_infra.release.orchestrator_phases as _flext_infra_release_orchestrator_phases
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator

    orchestrator_phases = _flext_infra_release_orchestrator_phases
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.release.orchestrator_phases import (
        FlextInfraReleaseOrchestratorPhases,
    )
_LAZY_IMPORTS = {
    "FlextInfraCliRelease": "flext_infra.release.cli",
    "FlextInfraReleaseConstants": "flext_infra.release._constants",
    "FlextInfraReleaseModels": "flext_infra.release._models",
    "FlextInfraReleaseOrchestrator": "flext_infra.release.orchestrator",
    "FlextInfraReleaseOrchestratorPhases": "flext_infra.release.orchestrator_phases",
    "_constants": "flext_infra.release._constants",
    "_models": "flext_infra.release._models",
    "cli": "flext_infra.release.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "orchestrator": "flext_infra.release.orchestrator",
    "orchestrator_phases": "flext_infra.release.orchestrator_phases",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliRelease",
    "FlextInfraReleaseConstants",
    "FlextInfraReleaseModels",
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseOrchestratorPhases",
    "_constants",
    "_models",
    "cli",
    "d",
    "e",
    "h",
    "orchestrator",
    "orchestrator_phases",
    "r",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
