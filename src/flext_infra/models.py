"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliModels

from flext_infra._models import FlextInfraCodegen
from flext_infra._models._config.base import FlextInfraConfigModels
from flext_infra._models.base import FlextInfraModelsBase
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.check import FlextInfraModelsCheck
from flext_infra._models.codegen_render import FlextInfraModelsCodegenRender
from flext_infra._models.codegen_toolchain import FlextInfraModelsCodegenToolchain
from flext_infra._models.codemod import FlextInfraModelsCodemod
from flext_infra._models.deps import FlextInfraModelsDeps
from flext_infra._models.deps_toml import FlextInfraModelsDepsToml
from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolConfig
from flext_infra._models.deps_tool_config_linters import (
    FlextInfraModelsDepsToolConfigLinters,
)
from flext_infra._models.deps_tool_config_project import (
    FlextInfraModelsDepsToolConfigProject,
)
from flext_infra._models.deps_tool_config_project_artifacts import (
    FlextInfraModelsDepsToolConfigProjectArtifacts,
)
from flext_infra._models.deps_tool_config_project_gitignore import (
    FlextInfraModelsDepsToolConfigProjectGitignore,
)
from flext_infra._models.deps_tool_config_project_mise import (
    FlextInfraModelsDepsToolConfigProjectMise,
)
from flext_infra._models.deps_tool_config_type_checkers import (
    FlextInfraModelsDepsToolConfigTypeCheckers,
)
from flext_infra._models.docs import FlextInfraModelsDocs
from flext_infra._models.docs_collection import FlextInfraModelsDocsCollection
from flext_infra._models.docs_generation import FlextInfraModelsDocsGeneration
from flext_infra._models.duplication import FlextInfraModelsDuplication
from flext_infra._models.gates import FlextInfraModelsGates
from flext_infra._models.git import FlextInfraModelsGit
from flext_infra._models.git_lane_inputs import FlextInfraModelsGitLaneInputs
from flext_infra._models.git_lane_ownership import FlextInfraModelsGitLaneOwnership
from flext_infra._models.layout import FlextInfraModelsLayout
from flext_infra._models.mise_toolchain import FlextInfraModelsMiseToolchain
from flext_infra._models.mise_toolchain_base import FlextInfraModelsMiseToolchainBase
from flext_infra._models.mixins import FlextInfraModelsMixins
from flext_infra._models.promoted import FlextInfraModelsPromoted
from flext_infra._models.refactor import FlextInfraModelsRefactor
from flext_infra._models.refactor_ast_grep import FlextInfraModelsRefactorGrep
from flext_infra._models.refactor_namespace_enforcer import (
    FlextInfraModelsNamespaceEnforcer,
)
from flext_infra._models.release import FlextInfraModelsRelease
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.rope_move import FlextInfraModelsRopeMove
from flext_infra._models.scan import FlextInfraModelsScan
from flext_infra._models.settings import FlextInfraSettingsModels
from flext_infra._models.sonarcloud import FlextInfraModelsSonarcloud
from flext_infra._models.testmon import FlextInfraModelsTestmon
from flext_infra._models.transformers import FlextInfraModelsTransformers
from flext_infra._models.validate import FlextInfraModelsCore
from flext_infra._models.workspace import FlextInfraModelsWorkspace
from flext_infra._models.worktree import FlextInfraModelsWorktree


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
