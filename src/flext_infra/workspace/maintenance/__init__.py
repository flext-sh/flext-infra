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
    from flext_infra.workspace.maintenance.cli import *
    from flext_infra.workspace.maintenance.python_version import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliMaintenance": "flext_infra.workspace.maintenance.cli",
    "FlextInfraPythonVersionEnforcer": "flext_infra.workspace.maintenance.python_version",
    "cli": "flext_infra.workspace.maintenance.cli",
    "logger": "flext_infra.workspace.maintenance.python_version",
    "python_version": "flext_infra.workspace.maintenance.python_version",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
