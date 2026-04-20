"""Constants for flext-infra.

Defines configuration constants and enumerations for infrastructure services
including validation rules, check types, and workspace settings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import c

from flext_infra import (
    FlextInfraConstantsBase,
    FlextInfraConstantsBasemk,
    FlextInfraConstantsCensus,
    FlextInfraConstantsCheck,
    FlextInfraConstantsCodegen,
    FlextInfraConstantsDeps,
    FlextInfraConstantsDocs,
    FlextInfraConstantsGithub,
    FlextInfraConstantsRefactor,
    FlextInfraConstantsRelease,
    FlextInfraConstantsRope,
    FlextInfraConstantsWorkspace,
)


class FlextInfraConstants(c):
    """Centralized constants for FLEXT infrastructure (Layer 0).

    Provides immutable, namespace-organized constants for infrastructure
    configuration, validation rules, check types, and workspace settings.

    Usage:
        >>> from flext_infra import c
        >>> c.Infra.STATUS_PASSED
        >>> c.Infra.VENV_BIN_REL
        >>> c.Infra.EXCLUDED_PROJECTS
    """

    class Infra(
        FlextInfraConstantsBase,
        FlextInfraConstantsCensus,
        FlextInfraConstantsBasemk,
        FlextInfraConstantsCheck,
        FlextInfraConstantsCodegen,
        FlextInfraConstantsRope,
        FlextInfraConstantsDeps,
        FlextInfraConstantsDocs,
        FlextInfraConstantsGithub,
        FlextInfraConstantsRefactor,
        FlextInfraConstantsRelease,
        FlextInfraConstantsWorkspace,
    ):
        """Merged infra-domain constants from all sub-packages."""


c = FlextInfraConstants
__all__: list[str] = ["FlextInfraConstants", "c"]
