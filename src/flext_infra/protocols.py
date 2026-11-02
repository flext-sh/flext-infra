# AUTO-GENERATED FILE - Source bootstrap protocol facade.
"""Structural contracts projected from source model declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliProtocols

from flext_infra._protocols.base import FlextInfraProtocolsBase
from flext_infra._protocols.census import FlextInfraProtocolsCensus
from flext_infra._protocols.check import FlextInfraProtocolsCheck
from flext_infra._protocols.codegen import FlextInfraProtocolsCodegen
from flext_infra._protocols.codemod import FlextInfraProtocolsCodemod
from flext_infra._protocols.config import FlextInfraProtocolsConfig
from flext_infra._protocols.deps import FlextInfraProtocolsDeps
from flext_infra._protocols.deps_toml import FlextInfraProtocolsDepsToml
from flext_infra._protocols.deps_tool_config import FlextInfraProtocolsDepsToolConfig
from flext_infra._protocols.deps_tool_config_linters import (
    FlextInfraProtocolsDepsToolConfigLinters,
)
from flext_infra._protocols.deps_tool_config_project import (
    FlextInfraProtocolsDepsToolConfigProject,
)
from flext_infra._protocols.deps_tool_config_project_artifacts import (
    FlextInfraProtocolsDepsToolConfigProjectArtifacts,
)
from flext_infra._protocols.deps_tool_config_project_gitignore import (
    FlextInfraProtocolsDepsToolConfigProjectGitignore,
)
from flext_infra._protocols.deps_tool_config_project_mise import (
    FlextInfraProtocolsDepsToolConfigProjectMise,
)
from flext_infra._protocols.deps_tool_config_type_checkers import (
    FlextInfraProtocolsDepsToolConfigTypeCheckers,
)
from flext_infra._protocols.docs import FlextInfraProtocolsDocs
from flext_infra._protocols.docs_collection import FlextInfraProtocolsDocsCollection
from flext_infra._protocols.docs_generation import FlextInfraProtocolsDocsGeneration
from flext_infra._protocols.duplication import FlextInfraProtocolsDuplication
from flext_infra._protocols.enforcement_catalog import (
    FlextInfraProtocolsEnforcementCatalog,
)
from flext_infra._protocols.gates import FlextInfraProtocolsGates
from flext_infra._protocols.git import FlextInfraProtocolsGit
from flext_infra._protocols.git_lane_inputs import FlextInfraProtocolsGitLaneInputs
from flext_infra._protocols.layout import FlextInfraProtocolsLayout
from flext_infra._protocols.mise_toolchain import FlextInfraProtocolsMiseToolchain
from flext_infra._protocols.mise_toolchain_base import (
    FlextInfraProtocolsMiseToolchainBase,
)
from flext_infra._protocols.mise_toolchain_repair import (
    FlextInfraProtocolsMiseToolchainRepair,
)
from flext_infra._protocols.mixins import FlextInfraProtocolsMixins
from flext_infra._protocols.promoted import FlextInfraProtocolsPromoted
from flext_infra._protocols.refactor import FlextInfraProtocolsRefactor
from flext_infra._protocols.refactor_ast_grep import FlextInfraProtocolsRefactorAstGrep
from flext_infra._protocols.refactor_namespace_enforcer import (
    FlextInfraProtocolsRefactorNamespaceEnforcer,
)
from flext_infra._protocols.release import FlextInfraProtocolsRelease
from flext_infra._protocols.rope import FlextInfraProtocolsRope
from flext_infra._protocols.rope_move import FlextInfraProtocolsRopeMove
from flext_infra._protocols.rope_runtime import FlextInfraProtocolsRopeRuntime
from flext_infra._protocols.scan import FlextInfraProtocolsScan
from flext_infra._protocols.settings import FlextInfraProtocolsSettings
from flext_infra._protocols.sonarcloud import FlextInfraProtocolsSonarcloud
from flext_infra._protocols.testmon import FlextInfraProtocolsTestmon
from flext_infra._protocols.transformers import FlextInfraProtocolsTransformers
from flext_infra._protocols.validate import FlextInfraProtocolsValidate
from flext_infra._protocols.workspace import FlextInfraProtocolsWorkspace
from flext_infra._protocols.worktree import FlextInfraProtocolsWorktree


class FlextInfraProtocols(FlextCliProtocols):
    """Structural contracts for flext-infra."""

    class Infra(
        FlextInfraProtocolsBase,
        FlextInfraProtocolsCensus,
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsCodegen,
        FlextInfraProtocolsCodemod,
        FlextInfraProtocolsConfig,
        FlextInfraProtocolsDeps,
        FlextInfraProtocolsDepsToml,
        FlextInfraProtocolsDepsToolConfig,
        FlextInfraProtocolsDepsToolConfigLinters,
        FlextInfraProtocolsDepsToolConfigProject,
        FlextInfraProtocolsDepsToolConfigProjectArtifacts,
        FlextInfraProtocolsDepsToolConfigProjectGitignore,
        FlextInfraProtocolsDepsToolConfigProjectMise,
        FlextInfraProtocolsDepsToolConfigTypeCheckers,
        FlextInfraProtocolsDocs,
        FlextInfraProtocolsDocsCollection,
        FlextInfraProtocolsDocsGeneration,
        FlextInfraProtocolsDuplication,
        FlextInfraProtocolsEnforcementCatalog,
        FlextInfraProtocolsGates,
        FlextInfraProtocolsGit,
        FlextInfraProtocolsGitLaneInputs,
        FlextInfraProtocolsLayout,
        FlextInfraProtocolsMiseToolchain,
        FlextInfraProtocolsMiseToolchainBase,
        FlextInfraProtocolsMiseToolchainRepair,
        FlextInfraProtocolsMixins,
        FlextInfraProtocolsPromoted,
        FlextInfraProtocolsRefactor,
        FlextInfraProtocolsRefactorAstGrep,
        FlextInfraProtocolsRefactorNamespaceEnforcer,
        FlextInfraProtocolsRelease,
        FlextInfraProtocolsRope,
        FlextInfraProtocolsRopeMove,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsScan,
        FlextInfraProtocolsSettings,
        FlextInfraProtocolsSonarcloud,
        FlextInfraProtocolsTestmon,
        FlextInfraProtocolsTransformers,
        FlextInfraProtocolsValidate,
        FlextInfraProtocolsWorkspace,
        FlextInfraProtocolsWorktree,
    ):
        """Aggregate source-derived protocol contracts."""


p = FlextInfraProtocols
__all__: list[str] = ["FlextInfraProtocols", "p"]
