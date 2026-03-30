# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Maintenance services.

Provides services for workspace maintenance, cleanup, and operational tasks.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.workspace.maintenance import (
        cli as cli,
        python_version as python_version,
    )
    from flext_infra.workspace.maintenance.cli import (
        FlextInfraCliMaintenance as FlextInfraCliMaintenance,
    )
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer as FlextInfraPythonVersionEnforcer,
        logger as logger,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliMaintenance": [
        "flext_infra.workspace.maintenance.cli",
        "FlextInfraCliMaintenance",
    ],
    "FlextInfraPythonVersionEnforcer": [
        "flext_infra.workspace.maintenance.python_version",
        "FlextInfraPythonVersionEnforcer",
    ],
    "cli": ["flext_infra.workspace.maintenance.cli", ""],
    "logger": ["flext_infra.workspace.maintenance.python_version", "logger"],
    "python_version": ["flext_infra.workspace.maintenance.python_version", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliMaintenance",
    "FlextInfraPythonVersionEnforcer",
    "cli",
    "logger",
    "python_version",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
