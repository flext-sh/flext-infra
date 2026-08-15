# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextInfraWorkspaceGeneratorBase
    from .detector import FlextInfraWorkspaceDetector
    from .environment_provenance import FlextInfraWorkspaceEnvironmentProvenance
    from .flext_binding import FlextInfraFlextBindingService
    from .orchestrator import FlextInfraOrchestratorService
    from .rope import FlextInfraRopeWorkspace
    from .sandbox_orchestrator import FlextInfraSandboxOrchestrator

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextInfraWorkspaceGeneratorBase",),
    ".detector": ("FlextInfraWorkspaceDetector",),
    ".environment_provenance": ("FlextInfraWorkspaceEnvironmentProvenance",),
    ".flext_binding": ("FlextInfraFlextBindingService",),
    ".orchestrator": ("FlextInfraOrchestratorService",),
    ".rope": ("FlextInfraRopeWorkspace",),
    ".sandbox_orchestrator": ("FlextInfraSandboxOrchestrator",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraFlextBindingService",
    "FlextInfraOrchestratorService",
    "FlextInfraRopeWorkspace",
    "FlextInfraSandboxOrchestrator",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceEnvironmentProvenance",
    "FlextInfraWorkspaceGeneratorBase",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
