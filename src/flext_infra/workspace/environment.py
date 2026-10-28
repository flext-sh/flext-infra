"""Extracted facade class for environment.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.workspace._environment import (
    FlextInfraWorkspaceEnvironmentProvenanceEditable,
    FlextInfraWorkspaceEnvironmentProvenanceModuleSource,
)


class FlextInfraWorkspaceEnvironment(
    FlextInfraWorkspaceEnvironmentProvenanceEditable,
    FlextInfraWorkspaceEnvironmentProvenanceModuleSource,
):
    """Facade for environment."""


__all__: list[str] = ["FlextInfraWorkspaceEnvironment"]
