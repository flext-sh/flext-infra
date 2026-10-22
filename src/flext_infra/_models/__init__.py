# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Models package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models import (
        _codegen as _codegen,
        _config as _config,
        _git as _git,
    )
    from flext_infra._models._codegen import (
        FlextInfraCodegen,
        FlextInfraModelsCodegenFixModels,
        FlextInfraModelsCodegenJournalModels,
        FlextInfraModelsCodegenLazyInitModels,
        FlextInfraModelsCodegenPipelineModels,
        FlextInfraModelsCodegenScaffoldModels,
        FlextInfraModelsCodegenTransactionModels,
    )
    from flext_infra._models._config import (
        FlextInfraConfigModels,
        FlextInfraConfigModelsArtifact,
        FlextInfraConfigModelsBeads,
        FlextInfraConfigModelsContexts,
        FlextInfraConfigModelsContract,
        FlextInfraConfigModelsMake,
        FlextInfraConfigModelsMakeClean,
        FlextInfraConfigModelsMakeDocs,
        FlextInfraConfigModelsProvider,
        FlextInfraConfigModelsRefactorCampaigns,
        FlextInfraConfigModelsRelease,
        FlextInfraConfigModelsRender,
        FlextInfraConfigModelsRepository,
        FlextInfraConfigModelsRoot,
        FlextInfraConfigModelsScaffold,
        FlextInfraConfigModelsSonarcloud,
        FlextInfraConfigModelsStatic,
        FlextInfraConfigModelsTemplates,
        FlextInfraConfigModelsWorkspace,
        FlextInfraExternalCacheDirectorySpec,
    )
    from flext_infra._models._git import (
        FlextInfraModelsGitIdentity,
        FlextInfraModelsGitWorktreeFacts,
        FlextInfraModelsGitWorktreeState,
    )
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
    from flext_infra._models.deps_typings import FlextInfraModelsDepsTypings
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
    from flext_infra._models.settings import FlextInfraSettingsModels
    from flext_infra._models.sonarcloud import FlextInfraModelsSonarcloud
    from flext_infra._models.testmon import FlextInfraModelsTestmon
    from flext_infra._models.transformers import FlextInfraModelsTransformers
    from flext_infra._models.validate import FlextInfraModelsCore
    from flext_infra._models.workspace import FlextInfraModelsWorkspace
    from flext_infra._models.worktree import FlextInfraModelsWorktree


__all__: tuple[str, ...] = (
    "FlextInfraCodegen",
    "FlextInfraConfigModels",
    "FlextInfraConfigModelsArtifact",
    "FlextInfraConfigModelsBeads",
    "FlextInfraConfigModelsContexts",
    "FlextInfraConfigModelsContract",
    "FlextInfraConfigModelsMake",
    "FlextInfraConfigModelsMakeClean",
    "FlextInfraConfigModelsMakeDocs",
    "FlextInfraConfigModelsProvider",
    "FlextInfraConfigModelsRefactorCampaigns",
    "FlextInfraConfigModelsRelease",
    "FlextInfraConfigModelsRender",
    "FlextInfraConfigModelsRepository",
    "FlextInfraConfigModelsRoot",
    "FlextInfraConfigModelsScaffold",
    "FlextInfraConfigModelsSonarcloud",
    "FlextInfraConfigModelsStatic",
    "FlextInfraConfigModelsTemplates",
    "FlextInfraConfigModelsWorkspace",
    "FlextInfraExternalCacheDirectorySpec",
    "FlextInfraModelsBase",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCheck",
    "FlextInfraModelsCodegenFixModels",
    "FlextInfraModelsCodegenJournalModels",
    "FlextInfraModelsCodegenLazyInitModels",
    "FlextInfraModelsCodegenPipelineModels",
    "FlextInfraModelsCodegenRender",
    "FlextInfraModelsCodegenScaffoldModels",
    "FlextInfraModelsCodegenToolchain",
    "FlextInfraModelsCodegenTransactionModels",
    "FlextInfraModelsCodemod",
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
    "FlextInfraModelsDepsTypings",
    "FlextInfraModelsDocs",
    "FlextInfraModelsDocsCollection",
    "FlextInfraModelsDocsGeneration",
    "FlextInfraModelsDuplication",
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
    "FlextInfraModelsSonarcloud",
    "FlextInfraModelsTestmon",
    "FlextInfraModelsTransformers",
    "FlextInfraModelsWorkspace",
    "FlextInfraModelsWorktree",
    "FlextInfraSettingsModels",
    "_codegen",
    "_config",
    "_git",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegen": "._codegen.base",
        "FlextInfraConfigModels": "._config.base",
        "FlextInfraConfigModelsArtifact": "._config.artifact",
        "FlextInfraConfigModelsBeads": "._config.beads",
        "FlextInfraConfigModelsContexts": "._config.contexts",
        "FlextInfraConfigModelsContract": "._config.contract",
        "FlextInfraConfigModelsMake": "._config.make",
        "FlextInfraConfigModelsMakeClean": "._config.make_clean",
        "FlextInfraConfigModelsMakeDocs": "._config.make_docs",
        "FlextInfraConfigModelsProvider": "._config.provider",
        "FlextInfraConfigModelsRefactorCampaigns": "._config.refactor_campaigns",
        "FlextInfraConfigModelsRelease": "._config.release",
        "FlextInfraConfigModelsRender": "._config.render",
        "FlextInfraConfigModelsRepository": "._config.repository",
        "FlextInfraConfigModelsRoot": "._config.root",
        "FlextInfraConfigModelsScaffold": "._config.scaffold",
        "FlextInfraConfigModelsSonarcloud": "._config.sonarcloud",
        "FlextInfraConfigModelsStatic": "._config.static",
        "FlextInfraConfigModelsTemplates": "._config.templates",
        "FlextInfraConfigModelsWorkspace": "._config.workspace",
        "FlextInfraExternalCacheDirectorySpec": "._config.external_cache",
        "FlextInfraModelsBase": ".base",
        "FlextInfraModelsCensus": ".census",
        "FlextInfraModelsCheck": ".check",
        "FlextInfraModelsCodegenFixModels": "._codegen.fix",
        "FlextInfraModelsCodegenJournalModels": "._codegen.journal",
        "FlextInfraModelsCodegenLazyInitModels": "._codegen.lazy_init",
        "FlextInfraModelsCodegenPipelineModels": "._codegen.pipeline",
        "FlextInfraModelsCodegenRender": ".codegen_render",
        "FlextInfraModelsCodegenScaffoldModels": "._codegen.scaffold",
        "FlextInfraModelsCodegenToolchain": ".codegen_toolchain",
        "FlextInfraModelsCodegenTransactionModels": "._codegen.transaction",
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
            ".deps_tool_config_project_gitignore"
        ),
        "FlextInfraModelsDepsToolConfigProjectMise": ".deps_tool_config_project_mise",
        "FlextInfraModelsDepsToolConfigTypeCheckers": ".deps_tool_config_type_checkers",
        "FlextInfraModelsDepsTypings": ".deps_typings",
        "FlextInfraModelsDocs": ".docs",
        "FlextInfraModelsDocsCollection": ".docs_collection",
        "FlextInfraModelsDocsGeneration": ".docs_generation",
        "FlextInfraModelsDuplication": ".duplication",
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
        "FlextInfraModelsWorktree": ".worktree",
        "FlextInfraSettingsModels": ".settings",
        "_codegen": "._codegen",
        "_config": "._config",
        "_git": "._git",
    }),
    public_exports=__all__,
)
