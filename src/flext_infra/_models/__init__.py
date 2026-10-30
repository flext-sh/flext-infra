# AUTO-GENERATED FILE — Regenerate with: make gen
"""models package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models._codegen.base import FlextInfraCodegen
    from flext_infra._models._codegen.fix import FlextInfraModelsCodegenFix
    from flext_infra._models._codegen.lazy_init import FlextInfraModelsCodegenLazyInit
    from flext_infra._models._codegen.pipeline import FlextInfraModelsCodegenPipeline
    from flext_infra._models._codegen.scaffold import FlextInfraModelsCodegenScaffold
    from flext_infra._models._codegen.transaction import (
        FlextInfraModelsCodegenTransaction,
    )
    from flext_infra._models._config.artifact import FlextInfraModelsConfigArtifact
    from flext_infra._models._config.base import FlextInfraModelsConfig
    from flext_infra._models._config.beads import FlextInfraModelsConfigBeads
    from flext_infra._models._config.contexts import FlextInfraModelsConfigContexts
    from flext_infra._models._config.contract import FlextInfraModelsConfigContract
    from flext_infra._models._config.external_cache import (
        FlextInfraExternalCacheDirectorySpec,
    )
    from flext_infra._models._config.make import FlextInfraModelsConfigMake
    from flext_infra._models._config.make_clean import FlextInfraModelsConfigMakeClean
    from flext_infra._models._config.make_docs import FlextInfraModelsConfigMakeDocs
    from flext_infra._models._config.provider import FlextInfraModelsConfigProvider
    from flext_infra._models._config.refactor_campaigns import (
        FlextInfraModelsConfigRefactorCampaigns,
    )
    from flext_infra._models._config.release import FlextInfraModelsConfigRelease
    from flext_infra._models._config.render import FlextInfraModelsConfigRender
    from flext_infra._models._config.repository import FlextInfraModelsConfigRepository
    from flext_infra._models._config.root import FlextInfraModelsConfigRoot
    from flext_infra._models._config.scaffold import FlextInfraModelsConfigScaffold
    from flext_infra._models._config.sonarcloud import FlextInfraModelsConfigSonarcloud
    from flext_infra._models._config.static import FlextInfraModelsConfigStatic
    from flext_infra._models._config.templates import FlextInfraModelsConfigTemplates
    from flext_infra._models._config.workspace import FlextInfraModelsConfigWorkspace
    from flext_infra._models._git.identity import FlextInfraModelsGitIdentity
    from flext_infra._models._git.worktree_facts import FlextInfraModelsGitWorktreeFacts
    from flext_infra._models._git.worktree_state import FlextInfraModelsGitWorktreeState
    from flext_infra._models.base import FlextInfraModelsBase
    from flext_infra._models.census import FlextInfraModelsCensus
    from flext_infra._models.check import FlextInfraModelsCheck
    from flext_infra._models.codegen_render import FlextInfraModelsCodegenRender
    from flext_infra._models.codegen_toolchain import FlextInfraModelsCodegenToolchain
    from flext_infra._models.codemod import FlextInfraModelsCodemod
    from flext_infra._models.collection import FlextInfraModelsDocsCollection
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
    from flext_infra._models.deps_tool_config_project_ignore import (
        FlextInfraModelsDepsToolConfigProjectGitignore,
    )
    from flext_infra._models.deps_tool_config_project_mise import (
        FlextInfraModelsDepsToolConfigProjectMise,
    )
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraModelsDepsToolConfigTypeCheckers,
    )
    from flext_infra._models.docs import FlextInfraModelsDocs
    from flext_infra._models.docs_generation import FlextInfraModelsDocsGeneration
    from flext_infra._models.duplication import FlextInfraModelsDuplication
    from flext_infra._models.enforcement_catalog import (
        FlextInfraModelsEnforcementCatalog,
    )
    from flext_infra._models.gates import FlextInfraModelsGates
    from flext_infra._models.git import FlextInfraModelsGit
    from flext_infra._models.git_lane_inputs import FlextInfraModelsGitLaneInputs
    from flext_infra._models.git_lane_ownership import FlextInfraModelsGitLaneOwnership
    from flext_infra._models.layout import FlextInfraModelsLayout
    from flext_infra._models.mise_toolchain import FlextInfraModelsMiseToolchain
    from flext_infra._models.mise_toolchain_base import (
        FlextInfraModelsMiseToolchainBase,
    )
    from flext_infra._models.mise_toolchain_repair import (
        FlextInfraModelsMiseToolchainRepair,
    )
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
    from flext_infra._models.settings import FlextInfraModelsSettings
    from flext_infra._models.sonarcloud import FlextInfraModelsSonarcloud
    from flext_infra._models.testmon import FlextInfraModelsTestmon
    from flext_infra._models.transformers import FlextInfraModelsTransformers
    from flext_infra._models.validate import FlextInfraModelsCore
    from flext_infra._models.workspace import FlextInfraModelsWorkspace
    from flext_infra._models.workspace_snapshot import FlextInfraModelsWorkspaceSnapshot
    from flext_infra._models.worktree import FlextInfraModelsWorktree


__all__: tuple[str, ...] = (
    "FlextInfraCodegen",
    "FlextInfraExternalCacheDirectorySpec",
    "FlextInfraModelsBase",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCheck",
    "FlextInfraModelsCodegenFix",
    "FlextInfraModelsCodegenLazyInit",
    "FlextInfraModelsCodegenPipeline",
    "FlextInfraModelsCodegenRender",
    "FlextInfraModelsCodegenScaffold",
    "FlextInfraModelsCodegenToolchain",
    "FlextInfraModelsCodegenTransaction",
    "FlextInfraModelsCodemod",
    "FlextInfraModelsConfig",
    "FlextInfraModelsConfigArtifact",
    "FlextInfraModelsConfigBeads",
    "FlextInfraModelsConfigContexts",
    "FlextInfraModelsConfigContract",
    "FlextInfraModelsConfigMake",
    "FlextInfraModelsConfigMakeClean",
    "FlextInfraModelsConfigMakeDocs",
    "FlextInfraModelsConfigProvider",
    "FlextInfraModelsConfigRefactorCampaigns",
    "FlextInfraModelsConfigRelease",
    "FlextInfraModelsConfigRender",
    "FlextInfraModelsConfigRepository",
    "FlextInfraModelsConfigRoot",
    "FlextInfraModelsConfigScaffold",
    "FlextInfraModelsConfigSonarcloud",
    "FlextInfraModelsConfigStatic",
    "FlextInfraModelsConfigTemplates",
    "FlextInfraModelsConfigWorkspace",
    "FlextInfraModelsCore",
    "FlextInfraModelsDeps",
    "FlextInfraModelsDepsToml",
    "FlextInfraModelsDepsToolConfig",
    "FlextInfraModelsDepsToolConfigLinters",
    "FlextInfraModelsDepsToolConfigProject",
    "FlextInfraModelsDepsToolConfigProjectArtifacts",
    "FlextInfraModelsDepsToolConfigProjectGitignore",
    "FlextInfraModelsDepsToolConfigProjectMise",
    "FlextInfraModelsDepsToolConfigTypeCheckers",
    "FlextInfraModelsDocs",
    "FlextInfraModelsDocsCollection",
    "FlextInfraModelsDocsGeneration",
    "FlextInfraModelsDuplication",
    "FlextInfraModelsEnforcementCatalog",
    "FlextInfraModelsGates",
    "FlextInfraModelsGit",
    "FlextInfraModelsGitIdentity",
    "FlextInfraModelsGitLaneInputs",
    "FlextInfraModelsGitLaneOwnership",
    "FlextInfraModelsGitWorktreeFacts",
    "FlextInfraModelsGitWorktreeState",
    "FlextInfraModelsLayout",
    "FlextInfraModelsMiseToolchain",
    "FlextInfraModelsMiseToolchainBase",
    "FlextInfraModelsMiseToolchainRepair",
    "FlextInfraModelsMixins",
    "FlextInfraModelsNamespaceEnforcer",
    "FlextInfraModelsPromoted",
    "FlextInfraModelsRefactor",
    "FlextInfraModelsRefactorGrep",
    "FlextInfraModelsRelease",
    "FlextInfraModelsRope",
    "FlextInfraModelsRopeMove",
    "FlextInfraModelsScan",
    "FlextInfraModelsSettings",
    "FlextInfraModelsSonarcloud",
    "FlextInfraModelsTestmon",
    "FlextInfraModelsTransformers",
    "FlextInfraModelsWorkspace",
    "FlextInfraModelsWorkspaceSnapshot",
    "FlextInfraModelsWorktree",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegen": "._codegen.base",
        "FlextInfraModelsConfig": "._config.base",
        "FlextInfraModelsConfigArtifact": "._config.artifact",
        "FlextInfraModelsConfigBeads": "._config.beads",
        "FlextInfraModelsConfigContexts": "._config.contexts",
        "FlextInfraModelsConfigContract": "._config.contract",
        "FlextInfraModelsConfigMake": "._config.make",
        "FlextInfraModelsConfigMakeClean": "._config.make_clean",
        "FlextInfraModelsConfigMakeDocs": "._config.make_docs",
        "FlextInfraModelsConfigProvider": "._config.provider",
        "FlextInfraModelsConfigRefactorCampaigns": "._config.refactor_campaigns",
        "FlextInfraModelsConfigRelease": "._config.release",
        "FlextInfraModelsConfigRender": "._config.render",
        "FlextInfraModelsConfigRepository": "._config.repository",
        "FlextInfraModelsConfigRoot": "._config.root",
        "FlextInfraModelsConfigScaffold": "._config.scaffold",
        "FlextInfraModelsConfigSonarcloud": "._config.sonarcloud",
        "FlextInfraModelsConfigStatic": "._config.static",
        "FlextInfraModelsConfigTemplates": "._config.templates",
        "FlextInfraModelsConfigWorkspace": "._config.workspace",
        "FlextInfraExternalCacheDirectorySpec": "._config.external_cache",
        "FlextInfraModelsBase": ".base",
        "FlextInfraModelsCensus": ".census",
        "FlextInfraModelsCheck": ".check",
        "FlextInfraModelsCodegenFix": "._codegen.fix",
        "FlextInfraModelsCodegenLazyInit": "._codegen.lazy_init",
        "FlextInfraModelsCodegenPipeline": "._codegen.pipeline",
        "FlextInfraModelsCodegenRender": ".codegen_render",
        "FlextInfraModelsCodegenScaffold": "._codegen.scaffold",
        "FlextInfraModelsCodegenToolchain": ".codegen_toolchain",
        "FlextInfraModelsCodegenTransaction": "._codegen.transaction",
        "FlextInfraModelsCodemod": ".codemod",
        "FlextInfraModelsCore": ".validate",
        "FlextInfraModelsDeps": ".deps",
        "FlextInfraModelsDepsToml": ".deps_toml",
        "FlextInfraModelsDepsToolConfig": ".deps_tool_config",
        "FlextInfraModelsDepsToolConfigLinters": ".deps_tool_config_linters",
        "FlextInfraModelsDepsToolConfigProject": ".deps_tool_config_project",
        "FlextInfraModelsDepsToolConfigProjectArtifacts": (
            ".deps_tool_config_project_artifacts"
        ),
        "FlextInfraModelsDepsToolConfigProjectGitignore": (
            ".deps_tool_config_project_ignore"
        ),
        "FlextInfraModelsDepsToolConfigProjectMise": ".deps_tool_config_project_mise",
        "FlextInfraModelsDepsToolConfigTypeCheckers": ".deps_tool_config_type_checkers",
        "FlextInfraModelsDocs": ".docs",
        "FlextInfraModelsDocsCollection": ".collection",
        "FlextInfraModelsDocsGeneration": ".docs_generation",
        "FlextInfraModelsDuplication": ".duplication",
        "FlextInfraModelsEnforcementCatalog": ".enforcement_catalog",
        "FlextInfraModelsGates": ".gates",
        "FlextInfraModelsGit": ".git",
        "FlextInfraModelsGitIdentity": "._git.identity",
        "FlextInfraModelsGitLaneInputs": ".git_lane_inputs",
        "FlextInfraModelsGitLaneOwnership": ".git_lane_ownership",
        "FlextInfraModelsGitWorktreeFacts": "._git.worktree_facts",
        "FlextInfraModelsGitWorktreeState": "._git.worktree_state",
        "FlextInfraModelsLayout": ".layout",
        "FlextInfraModelsMiseToolchain": ".mise_toolchain",
        "FlextInfraModelsMiseToolchainBase": ".mise_toolchain_base",
        "FlextInfraModelsMiseToolchainRepair": ".mise_toolchain_repair",
        "FlextInfraModelsMixins": ".mixins",
        "FlextInfraModelsNamespaceEnforcer": ".refactor_namespace_enforcer",
        "FlextInfraModelsPromoted": ".promoted",
        "FlextInfraModelsRefactor": ".refactor",
        "FlextInfraModelsRefactorGrep": ".refactor_ast_grep",
        "FlextInfraModelsRelease": ".release",
        "FlextInfraModelsRope": ".rope",
        "FlextInfraModelsRopeMove": ".rope_move",
        "FlextInfraModelsScan": ".scan",
        "FlextInfraModelsSonarcloud": ".sonarcloud",
        "FlextInfraModelsTestmon": ".testmon",
        "FlextInfraModelsTransformers": ".transformers",
        "FlextInfraModelsWorkspace": ".workspace",
        "FlextInfraModelsWorkspaceSnapshot": ".workspace_snapshot",
        "FlextInfraModelsWorktree": ".worktree",
        "FlextInfraModelsSettings": ".settings",
    }),
    public_exports=__all__,
)
