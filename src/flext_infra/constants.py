"""Constants facade for flext-infra — c.Infra project namespace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import c
from flext_infra._constants.base import FlextInfraConstantsBase
from flext_infra._constants.basemk import FlextInfraConstantsBasemk
from flext_infra._constants.census import FlextInfraConstantsCensus
from flext_infra._constants.check import FlextInfraConstantsCheck
from flext_infra._constants.cli import FlextInfraConstantsCli
from flext_infra._constants.codegen import FlextInfraConstantsCodegen
from flext_infra._constants.deps import FlextInfraConstantsDeps
from flext_infra._constants.detectors import FlextInfraConstantsDetectors
from flext_infra._constants.docs import FlextInfraConstantsDocs
from flext_infra._constants.github import FlextInfraConstantsGithub
from flext_infra._constants.refactor import FlextInfraConstantsRefactor
from flext_infra._constants.release import FlextInfraConstantsRelease
from flext_infra._constants.rope import FlextInfraConstantsRope
from flext_infra._constants.workspace import FlextInfraConstantsWorkspace


class FlextInfraConstants(c):
    """Infra constants facade — access via c.Infra.*."""

    class Infra(
        FlextInfraConstantsBase,
        FlextInfraConstantsCensus,
        FlextInfraConstantsBasemk,
        FlextInfraConstantsCheck,
        FlextInfraConstantsCli,
        FlextInfraConstantsCodegen,
        FlextInfraConstantsRope,
        FlextInfraConstantsDeps,
        FlextInfraConstantsDetectors,
        FlextInfraConstantsDocs,
        FlextInfraConstantsGithub,
        FlextInfraConstantsRefactor,
        FlextInfraConstantsRelease,
        FlextInfraConstantsWorkspace,
    ):
        """Infra-domain constants — merged mixin namespace."""


c = FlextInfraConstants
__all__: tuple[str, ...] = ("FlextInfraConstants", "c")
