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
    "python_version": "flext_infra.workspace.maintenance.python_version",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
