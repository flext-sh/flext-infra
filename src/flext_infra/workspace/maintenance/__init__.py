# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Maintenance package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.workspace.maintenance.cli as _flext_infra_workspace_maintenance_cli

    cli = _flext_infra_workspace_maintenance_cli
    import flext_infra.workspace.maintenance.python_version as _flext_infra_workspace_maintenance_python_version
    from flext_infra.workspace.maintenance.cli import FlextInfraCliMaintenance

    python_version = _flext_infra_workspace_maintenance_python_version
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer,
        logger,
    )
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
    "logger": ("flext_infra.workspace.maintenance.python_version", "logger"),
    "python_version": "flext_infra.workspace.maintenance.python_version",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliMaintenance",
    "FlextInfraPythonVersionEnforcer",
    "cli",
    "d",
    "e",
    "h",
    "logger",
    "python_version",
    "r",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
