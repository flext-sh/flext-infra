# AUTO-GENERATED FILE — Regenerate with: make gen
"""Maintenance package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.maintenance.clean import FlextInfraMaintenanceClean
    from flext_infra.maintenance.python_version import (
        FlextInfraMaintenancePythonVersion,
    )
    from flext_infra.maintenance.sonarcloud import FlextInfraMaintenanceSonarcloud
    from flext_infra.maintenance.sonarcloud_client import (
        FlextInfraMaintenanceSonarcloudClient,
    )
    from flext_infra.maintenance.sonarcloud_issues import (
        FlextInfraMaintenanceSonarcloudIssues,
    )


__all__: tuple[str, ...] = (
    "FlextInfraMaintenanceClean",
    "FlextInfraMaintenancePythonVersion",
    "FlextInfraMaintenanceSonarcloud",
    "FlextInfraMaintenanceSonarcloudClient",
    "FlextInfraMaintenanceSonarcloudIssues",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraMaintenanceClean": ".clean",
        "FlextInfraMaintenancePythonVersion": ".python_version",
        "FlextInfraMaintenanceSonarcloudClient": ".sonarcloud_client",
        "FlextInfraMaintenanceSonarcloudIssues": ".sonarcloud_issues",
        "FlextInfraMaintenanceSonarcloud": ".sonarcloud",
    }),
    public_exports=__all__,
)
