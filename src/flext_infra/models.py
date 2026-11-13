# AUTO-GENERATED FILE — Regenerate with: make gen
"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from flext_cli import FlextCliModels

from flext_infra._models import (
    FlextInfraModelsCensus,
    FlextInfraModelsCheck,
    FlextInfraModelsCodegen,
    FlextInfraModelsCodemod,
    FlextInfraModelsCore,
    FlextInfraModelsDeps,
    FlextInfraModelsDocs,
    FlextInfraModelsEnforcementCatalog,
    FlextInfraModelsGateAdmission,
    FlextInfraModelsGates,
    FlextInfraModelsGit,
    FlextInfraModelsLayout,
    FlextInfraModelsMiseToolchainBase,
    FlextInfraModelsMiseToolchainRepair,
    FlextInfraModelsMixins,
    FlextInfraModelsPromoted,
    FlextInfraModelsRefactor,
    FlextInfraModelsRelease,
    FlextInfraModelsRope,
    FlextInfraModelsRopeMove,
    FlextInfraModelsScan,
    FlextInfraModelsSettings,
    FlextInfraModelsSonarcloud,
    FlextInfraModelsTestmon,
    FlextInfraModelsTransformers,
    FlextInfraModelsWorkspace,
    FlextInfraModelsWorkspaceSnapshot,
    FlextInfraModelsWorktree,
)
from flext_infra._models._codegen import FlextInfraCodegen
from flext_infra._models._config import FlextInfraModelsConfig


class FlextInfraModels(FlextCliModels):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraCodegen,
        FlextInfraModelsCensus,
        FlextInfraModelsCheck,
        FlextInfraModelsCodegen,
        FlextInfraModelsCodemod,
        FlextInfraModelsDeps,
        FlextInfraModelsDocs,
        FlextInfraModelsEnforcementCatalog,
        FlextInfraModelsGateAdmission,
        FlextInfraModelsGates,
        FlextInfraModelsGit,
        FlextInfraModelsLayout,
        FlextInfraModelsMiseToolchainBase,
        FlextInfraModelsMiseToolchainRepair,
        FlextInfraModelsMixins,
        FlextInfraModelsPromoted,
        FlextInfraModelsRefactor,
        FlextInfraModelsRelease,
        FlextInfraModelsRope,
        FlextInfraModelsRopeMove,
        FlextInfraModelsScan,
        FlextInfraModelsSettings,
        FlextInfraModelsSonarcloud,
        FlextInfraModelsTestmon,
        FlextInfraModelsTransformers,
        FlextInfraModelsCore,
        FlextInfraModelsWorkspace,
        FlextInfraModelsWorkspaceSnapshot,
        FlextInfraModelsWorktree,
        FlextInfraModelsConfig,
    ):
        """Infrastructure-domain models - all classes exposed directly."""

        if TYPE_CHECKING:
            ModScanCounts: TypeAlias = FlextInfraModelsScan.ModScanCounts
            ModOccurrenceReport: TypeAlias = FlextInfraModelsScan.ModOccurrenceReport


m = FlextInfraModels

__all__: list[str] = ["FlextInfraModels", "m"]
