"""Constants facade for flext-infra — c.Infra project namespace.

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
    FlextInfraConstantsSharedInfra,
    FlextInfraConstantsWorkspace,
)


class FlextInfraConstants(c):
    """Infra constants facade — access via c.Infra.*."""

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
        FlextInfraConstantsSharedInfra,
        FlextInfraConstantsWorkspace,
    ):
        """Infra-domain constants — merged mixin namespace."""


c = FlextInfraConstants
__all__: list[str] = ["FlextInfraConstants", "c"]
