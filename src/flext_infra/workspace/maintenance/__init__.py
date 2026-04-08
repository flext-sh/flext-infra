# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Maintenance package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCliMaintenance": (
        "flext_infra.workspace.maintenance.cli",
        "FlextInfraCliMaintenance",
    ),
    "FlextInfraPythonVersionEnforcer": (
        "flext_infra.workspace.maintenance.python_version",
        "FlextInfraPythonVersionEnforcer",
    ),
    "cli": "flext_infra.workspace.maintenance.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "python_version": "flext_infra.workspace.maintenance.python_version",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
