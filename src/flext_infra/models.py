# AUTO-GENERATED FILE — Regenerate with: make gen
"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliModels

from flext_infra._models._codegen import FlextInfraCodegen
from flext_infra._models._config import FlextInfraModelsConfig
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.check import FlextInfraModelsCheck
from flext_infra._models.codegen import FlextInfraModelsCodegen
from flext_infra._models.codemod import FlextInfraModelsCodemod
from flext_infra._models.deps import FlextInfraModelsDeps
from flext_infra._models.docs import FlextInfraModelsDocs
from flext_infra._models.enforcement_catalog import FlextInfraModelsEnforcementCatalog
from flext_infra._models.gates import FlextInfraModelsGates
from flext_infra._models.git import FlextInfraModelsGit
from flext_infra._models.layout import FlextInfraModelsLayout
from flext_infra._models.mise_toolchain_base import FlextInfraModelsMiseToolchainBase
from flext_infra._models.mise_toolchain_repair import (
    FlextInfraModelsMiseToolchainRepair,
)
from flext_infra._models.mixins import FlextInfraModelsMixins
from flext_infra._models.promoted import FlextInfraModelsPromoted
from flext_infra._models.refactor import FlextInfraModelsRefactor
from flext_infra._models.release import FlextInfraModelsRelease
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.rope_move import FlextInfraModelsRopeMove
from flext_infra._models.scan import FlextInfraModelsScan
from flext_infra._models.settings import FlextInfraModelsSettings
from flext_infra._models.sonarcloud import FlextInfraModelsSonarcloud
from flext_infra._models.testmon import FlextInfraModelsTestmon
from flext_infra._models.transformers import FlextInfraModelsTransformers
from flext_infra._models.validate import FlextInfraModelsCore
from flext_infra._models.workspace import FlextInfraModelsWorkspace
from flext_infra._models.workspace_snapshot import FlextInfraModelsWorkspaceSnapshot
from flext_infra._models.worktree import FlextInfraModelsWorktree


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


m = FlextInfraModels

__all__: list[str] = ["FlextInfraModels", "m"]
