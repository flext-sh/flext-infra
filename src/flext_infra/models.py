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
    )
from flext_infra._models._config import FlextInfraConfigModels
from flext_infra._models import FlextInfraModelsBase
from flext_infra._models import FlextInfraModelsCensus
from flext_infra._models import FlextInfraModelsCheck
from flext_infra._models import FlextInfraModelsCodegenRender
from flext_infra._models import FlextInfraModelsCodegenToolchain
from flext_infra._models import FlextInfraModelsCodemod
from flext_infra._models import FlextInfraModelsDeps
from flext_infra._models import FlextInfraModelsDepsToml
from flext_infra._models import FlextInfraModelsDepsToolConfig
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigLinters,
)
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigProject,
)
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigProjectArtifacts,
)
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigProjectGitignore,
)
from flext_infra._models import FlextInfraModelsDocs
from flext_infra._models import FlextInfraModelsDocsCollection
from flext_infra._models import FlextInfraModelsDocsGeneration
from flext_infra._models import FlextInfraModelsDuplication
from flext_infra._models import FlextInfraModelsGates
from flext_infra._models import FlextInfraModelsGit
from flext_infra._models import FlextInfraModelsGitLaneInputs
from flext_infra._models import FlextInfraModelsGitLaneOwnership
from flext_infra._models import FlextInfraModelsLayout
from flext_infra._models import FlextInfraModelsMiseToolchain
from flext_infra._models import FlextInfraModelsMiseToolchainBase
from flext_infra._models import FlextInfraModelsMixins
from flext_infra._models import FlextInfraModelsPromoted
from flext_infra._models import FlextInfraModelsRefactor
from flext_infra._models import FlextInfraModelsRefactorGrep
from flext_infra._models import (
    FlextInfraModelsNamespaceEnforcer,
)
from flext_infra._models import FlextInfraModelsRelease
from flext_infra._models import FlextInfraModelsRope
from flext_infra._models import FlextInfraModelsRopeMove
from flext_infra._models import FlextInfraModelsScan
from flext_infra._models import FlextInfraSettingsModels
from flext_infra._models import FlextInfraModelsSonarcloud
from flext_infra._models import FlextInfraModelsTestmon
from flext_infra._models import FlextInfraModelsTransformers
from flext_infra._models import FlextInfraModelsCore
from flext_infra._models import FlextInfraModelsWorkspace
from flext_infra._models import FlextInfraModelsWorktree
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigProjectMise,
)
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigTypeCheckers,
)


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
