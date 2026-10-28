# AUTO-GENERATED FILE — Regenerate with: make gen
"""Constants facade for flext-infra — c.Infra project namespace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliConstants

from flext_infra._constants import (
    FlextInfraConstantsBase,
    FlextInfraConstantsCensus,
    FlextInfraConstantsCheck,
    FlextInfraConstantsCli,
    FlextInfraConstantsCodegen,
    FlextInfraConstantsCodegenDetection,
    FlextInfraConstantsCodegenLazy,
    FlextInfraConstantsCodegenProject,
    FlextInfraConstantsCodegenRenderNames,
    FlextInfraConstantsConfig,
    FlextInfraConstantsDeps,
    FlextInfraConstantsDocs,
    FlextInfraConstantsGit,
    FlextInfraConstantsMake,
    FlextInfraConstantsNamespace,
    FlextInfraConstantsPromoted,
    FlextInfraConstantsPromotedMessages,
    FlextInfraConstantsPytest,
    FlextInfraConstantsRefactor,
    FlextInfraConstantsRelease,
    FlextInfraConstantsRope,
    FlextInfraConstantsSharedInfra,
    FlextInfraConstantsSourceCode,
    FlextInfraConstantsWorkspace,
)


class FlextInfraConstants(FlextCliConstants):
    """Infra constants facade — access via c.Infra.*."""

    class Infra(
        FlextInfraConstantsBase,
        FlextInfraConstantsSharedInfra,
        FlextInfraConstantsMake,
        FlextInfraConstantsCensus,
        FlextInfraConstantsCheck,
        FlextInfraConstantsCli,
        FlextInfraConstantsCodegen,
        FlextInfraConstantsCodegenLazy,
        FlextInfraConstantsCodegenDetection,
        FlextInfraConstantsCodegenRenderNames,
        FlextInfraConstantsCodegenProject,
        FlextInfraConstantsDeps,
        FlextInfraConstantsConfig,
        FlextInfraConstantsSourceCode,
        FlextInfraConstantsDocs,
        FlextInfraConstantsGit,
        FlextInfraConstantsNamespace,
        FlextInfraConstantsPromoted,
        FlextInfraConstantsPromotedMessages,
        FlextInfraConstantsPytest,
        FlextInfraConstantsRefactor,
        FlextInfraConstantsRelease,
        FlextInfraConstantsRope,
        FlextInfraConstantsWorkspace,
    ):
        """Infra-domain constants — merged mixin namespace."""


c = FlextInfraConstants
__all__: list[str] = ["FlextInfraConstants", "c"]
