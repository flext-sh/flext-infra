# AUTO-GENERATED FILE — Regenerate with: make gen
"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliModels

from flext_infra._models import (
    FlextInfraCodegen,
    FlextInfraModelsBase,
    FlextInfraModelsCensus,
    FlextInfraModelsCheck,
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsCodemod,
    FlextInfraModelsCore,
    FlextInfraModelsDeps,
    FlextInfraModelsDepsToml,
    FlextInfraModelsDepsToolConfig,
    FlextInfraModelsDepsToolConfigLinters,
    FlextInfraModelsDepsToolConfigProject,
    FlextInfraModelsDepsToolConfigProjectArtifacts,
    FlextInfraModelsDepsToolConfigProjectGitignore,
    FlextInfraModelsDepsToolConfigProjectMise,
    FlextInfraModelsDepsToolConfigTypeCheckers,
    FlextInfraModelsDocs,
    FlextInfraModelsDocsCollection,
    FlextInfraModelsDocsGeneration,
    FlextInfraModelsDuplication,
    FlextInfraModelsGates,
    FlextInfraModelsGit,
    FlextInfraModelsGitLaneInputs,
    FlextInfraModelsGitLaneOwnership,
    FlextInfraModelsLayout,
    FlextInfraModelsMiseToolchain,
    FlextInfraModelsMiseToolchainBase,
    FlextInfraModelsMiseToolchainRepair,
    FlextInfraModelsMixins,
    FlextInfraModelsNamespaceEnforcer,
    FlextInfraModelsPromoted,
    FlextInfraModelsRefactor,
    FlextInfraModelsRefactorGrep,
    FlextInfraModelsRelease,
    FlextInfraModelsRope,
    FlextInfraModelsRopeMove,
    FlextInfraModelsScan,
    FlextInfraModelsSonarcloud,
    FlextInfraModelsTestmon,
    FlextInfraModelsTransformers,
    FlextInfraModelsWorkspace,
    FlextInfraModelsWorktree,
    FlextInfraSettingsModels,
)
from flext_infra._models._config import FlextInfraConfigModels


class FlextInfraModels(FlextCliModels):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraModelsCensus,
        FlextInfraModelsCheck,
        FlextInfraModelsCodemod,
        FlextInfraModelsDeps,
        FlextInfraModelsDepsToolConfig,
        FlextInfraModelsDepsToolConfigLinters,
        FlextInfraModelsDepsToolConfigProject,
        FlextInfraModelsDepsToolConfigProjectArtifacts,
        FlextInfraModelsDepsToolConfigProjectGitignore,
        FlextInfraModelsDepsToolConfigProjectMise,
        FlextInfraModelsDepsToolConfigTypeCheckers,
        FlextInfraModelsDepsToml,
        FlextInfraModelsDocs,
        FlextInfraModelsDocsGeneration,
        FlextInfraModelsDocsCollection,
        FlextInfraModelsGates,
        FlextInfraModelsDuplication,
        FlextInfraModelsGit,
        FlextInfraModelsGitLaneOwnership,
        FlextInfraModelsGitLaneInputs,
        FlextInfraModelsLayout,
        FlextInfraModelsMiseToolchainBase,
        FlextInfraModelsMiseToolchainRepair,
        FlextInfraModelsMixins,
        FlextInfraModelsPromoted,
        FlextInfraModelsBase,
        FlextInfraModelsRefactor,
        FlextInfraModelsRefactorGrep,
        FlextInfraModelsNamespaceEnforcer,
        FlextInfraModelsRelease,
        FlextInfraModelsRope,
        FlextInfraModelsRopeMove,
        FlextInfraModelsScan,
        FlextInfraSettingsModels,
        FlextInfraModelsSonarcloud,
        FlextInfraModelsTestmon,
        FlextInfraModelsTransformers,
        FlextInfraModelsCore,
        FlextInfraModelsWorkspace,
        FlextInfraModelsWorktree,
        FlextInfraConfigModels,
        FlextInfraModelsMiseToolchain,
        FlextInfraCodegen,
        FlextInfraModelsCodegenToolchain,
        FlextInfraModelsCodegenRender,
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__: list[str] = ["FlextInfraModels", "m"]
