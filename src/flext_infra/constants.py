"""Constants for flext-infra.

Defines configuration constants and enumerations for infrastructure services
including validation rules, check types, and workspace settings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core import FlextConstants

from flext_infra import (
    FlextInfraBasemkConstants,
    FlextInfraCheckConstants,
    FlextInfraCodegenConstants,
    FlextInfraConstantsBase,
    FlextInfraCoreConstants,
    FlextInfraDepsConstants,
    FlextInfraDocsConstants,
    FlextInfraGithubConstants,
    FlextInfraRefactorConstants,
    FlextInfraReleaseConstants,
    FlextInfraSharedInfraConstants,
    FlextInfraWorkspaceConstants,
)


class FlextInfraConstants(FlextConstants):
    """Centralized constants for FLEXT infrastructure (Layer 0).

    Provides immutable, namespace-organized constants for infrastructure
    configuration, validation rules, check types, and workspace settings.

    Usage:
        >>> from flext_infra import c
        >>> c.Infra.Status.PASSED
        >>> c.Infra.Paths.VENV_BIN_REL
        >>> c.Infra.EXCLUDED_PROJECTS
    """

    class Infra(
        FlextInfraSharedInfraConstants,
        FlextInfraBasemkConstants,
        FlextInfraCheckConstants,
        FlextInfraCodegenConstants,
        FlextInfraCoreConstants,
        FlextInfraDepsConstants,
        FlextInfraDocsConstants,
        FlextInfraGithubConstants,
        FlextInfraRefactorConstants,
        FlextInfraReleaseConstants,
        FlextInfraWorkspaceConstants,
        FlextInfraConstantsBase,
    ):
        """Merged infra-domain constants from all sub-packages."""


c = FlextInfraConstants
__all__ = ["FlextInfraConstants", "c"]
