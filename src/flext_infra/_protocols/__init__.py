# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Protocols package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols.base import FlextInfraProtocolsBase
    from flext_infra._protocols.census import FlextInfraProtocolsCensus
    from flext_infra._protocols.check import FlextInfraProtocolsCheck
    from flext_infra._protocols.codegen import FlextInfraProtocolsCodegen
    from flext_infra._protocols.codegen_render import FlextInfraProtocolsCodegenRender
    from flext_infra._protocols.codegen_toolchain import (
        FlextInfraProtocolsCodegenToolchain,
    )
    from flext_infra._protocols.codemod import FlextInfraProtocolsCodemod
    from flext_infra._protocols.config import FlextInfraProtocolsConfig
    from flext_infra._protocols.deps import FlextInfraProtocolsDeps
    from flext_infra._protocols.deps_toml import FlextInfraProtocolsDepsToml
    from flext_infra._protocols.deps_tool_config import (
        FlextInfraProtocolsDepsToolConfig,
    )
    from flext_infra._protocols.deps_tool_config_linters import (
        FlextInfraProtocolsDepsToolConfigLinters,
    )
    from flext_infra._protocols.deps_tool_config_project import (
        FlextInfraProtocolsDepsToolConfigProject,
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
    from flext_infra._protocols.gate_admission import FlextInfraProtocolsGateAdmission
    from flext_infra._protocols.gates import FlextInfraProtocolsGates
    from flext_infra._protocols.git import FlextInfraProtocolsGit
    from flext_infra._protocols.git_lane_inputs import FlextInfraProtocolsGitLaneInputs
    from flext_infra._protocols.git_lane_ownership import (
        FlextInfraProtocolsGitLaneOwnership,
    )
    from flext_infra._protocols.layout import FlextInfraProtocolsLayout
    from flext_infra._protocols.mise_toolchain import FlextInfraProtocolsMiseToolchain
    from flext_infra._protocols.mise_toolchain_base import (
        FlextInfraProtocolsMiseToolchainBase,
    )
    from flext_infra._protocols.mise_toolchain_repair import (
        FlextInfraProtocolsMiseToolchainRepair,
    )
    from flext_infra._protocols.mixins import FlextInfraProtocolsMixins
    from flext_infra._protocols.project_artifacts import (
        FlextInfraProtocolsProjectArtifacts,
    )
    from flext_infra._protocols.project_gitignore import (
        FlextInfraProtocolsProjectGitignore,
    )
    from flext_infra._protocols.promoted import FlextInfraProtocolsPromoted
    from flext_infra._protocols.refactor import FlextInfraProtocolsRefactor
    from flext_infra._protocols.refactor_ast_grep import (
        FlextInfraProtocolsRefactorAstGrep,
    )
    from flext_infra._protocols.refactor_namespace_enforcer import (
        FlextInfraProtocolsRefactorNamespaceEnforcer,
    )
    from flext_infra._protocols.release import FlextInfraProtocolsRelease
    from flext_infra._protocols.release_forge import FlextInfraProtocolsReleaseForge
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
    from flext_infra._protocols.workspace_snapshot import (
        FlextInfraProtocolsWorkspaceSnapshot,
    )
    from flext_infra._protocols.worktree import FlextInfraProtocolsWorktree


__all__: tuple[str, ...] = (
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsCensus",
    "FlextInfraProtocolsCheck",
    "FlextInfraProtocolsCodegen",
    "FlextInfraProtocolsCodegenRender",
    "FlextInfraProtocolsCodegenToolchain",
    "FlextInfraProtocolsCodemod",
    "FlextInfraProtocolsConfig",
    "FlextInfraProtocolsDeps",
    "FlextInfraProtocolsDepsToml",
    "FlextInfraProtocolsDepsToolConfig",
    "FlextInfraProtocolsDepsToolConfigLinters",
    "FlextInfraProtocolsDepsToolConfigProject",
    "FlextInfraProtocolsDepsToolConfigProjectMise",
    "FlextInfraProtocolsDepsToolConfigTypeCheckers",
    "FlextInfraProtocolsDocs",
    "FlextInfraProtocolsDocsCollection",
    "FlextInfraProtocolsDocsGeneration",
    "FlextInfraProtocolsDuplication",
    "FlextInfraProtocolsEnforcementCatalog",
    "FlextInfraProtocolsGateAdmission",
    "FlextInfraProtocolsGates",
    "FlextInfraProtocolsGit",
    "FlextInfraProtocolsGitLaneInputs",
    "FlextInfraProtocolsGitLaneOwnership",
    "FlextInfraProtocolsLayout",
    "FlextInfraProtocolsMiseToolchain",
    "FlextInfraProtocolsMiseToolchainBase",
    "FlextInfraProtocolsMiseToolchainRepair",
    "FlextInfraProtocolsMixins",
    "FlextInfraProtocolsProjectArtifacts",
    "FlextInfraProtocolsProjectGitignore",
    "FlextInfraProtocolsPromoted",
    "FlextInfraProtocolsRefactor",
    "FlextInfraProtocolsRefactorAstGrep",
    "FlextInfraProtocolsRefactorNamespaceEnforcer",
    "FlextInfraProtocolsRelease",
    "FlextInfraProtocolsReleaseForge",
    "FlextInfraProtocolsRope",
    "FlextInfraProtocolsRopeMove",
    "FlextInfraProtocolsRopeRuntime",
    "FlextInfraProtocolsScan",
    "FlextInfraProtocolsSettings",
    "FlextInfraProtocolsSonarcloud",
    "FlextInfraProtocolsTestmon",
    "FlextInfraProtocolsTransformers",
    "FlextInfraProtocolsValidate",
    "FlextInfraProtocolsWorkspace",
    "FlextInfraProtocolsWorkspaceSnapshot",
    "FlextInfraProtocolsWorktree",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraProtocolsBase": ".base",
        "FlextInfraProtocolsCensus": ".census",
        "FlextInfraProtocolsCheck": ".check",
        "FlextInfraProtocolsCodegen": ".codegen",
        "FlextInfraProtocolsCodegenRender": ".codegen_render",
        "FlextInfraProtocolsCodegenToolchain": ".codegen_toolchain",
        "FlextInfraProtocolsCodemod": ".codemod",
        "FlextInfraProtocolsConfig": ".config",
        "FlextInfraProtocolsDeps": ".deps",
        "FlextInfraProtocolsDepsToml": ".deps_toml",
        "FlextInfraProtocolsDepsToolConfig": ".deps_tool_config",
        "FlextInfraProtocolsDepsToolConfigLinters": ".deps_tool_config_linters",
        "FlextInfraProtocolsDepsToolConfigProject": ".deps_tool_config_project",
        "FlextInfraProtocolsDepsToolConfigProjectMise": (
            ".deps_tool_config_project_mise"
        ),
        "FlextInfraProtocolsDepsToolConfigTypeCheckers": (
            ".deps_tool_config_type_checkers"
        ),
        "FlextInfraProtocolsDocs": ".docs",
        "FlextInfraProtocolsDocsCollection": ".docs_collection",
        "FlextInfraProtocolsDocsGeneration": ".docs_generation",
        "FlextInfraProtocolsDuplication": ".duplication",
        "FlextInfraProtocolsEnforcementCatalog": ".enforcement_catalog",
        "FlextInfraProtocolsGateAdmission": ".gate_admission",
        "FlextInfraProtocolsGates": ".gates",
        "FlextInfraProtocolsGit": ".git",
        "FlextInfraProtocolsGitLaneInputs": ".git_lane_inputs",
        "FlextInfraProtocolsGitLaneOwnership": ".git_lane_ownership",
        "FlextInfraProtocolsLayout": ".layout",
        "FlextInfraProtocolsMiseToolchain": ".mise_toolchain",
        "FlextInfraProtocolsMiseToolchainBase": ".mise_toolchain_base",
        "FlextInfraProtocolsMiseToolchainRepair": ".mise_toolchain_repair",
        "FlextInfraProtocolsMixins": ".mixins",
        "FlextInfraProtocolsProjectArtifacts": ".project_artifacts",
        "FlextInfraProtocolsProjectGitignore": ".project_gitignore",
        "FlextInfraProtocolsPromoted": ".promoted",
        "FlextInfraProtocolsRefactor": ".refactor",
        "FlextInfraProtocolsRefactorAstGrep": ".refactor_ast_grep",
        "FlextInfraProtocolsRefactorNamespaceEnforcer": ".refactor_namespace_enforcer",
        "FlextInfraProtocolsRelease": ".release",
        "FlextInfraProtocolsReleaseForge": ".release_forge",
        "FlextInfraProtocolsRope": ".rope",
        "FlextInfraProtocolsRopeMove": ".rope_move",
        "FlextInfraProtocolsRopeRuntime": ".rope_runtime",
        "FlextInfraProtocolsScan": ".scan",
        "FlextInfraProtocolsSettings": ".settings",
        "FlextInfraProtocolsSonarcloud": ".sonarcloud",
        "FlextInfraProtocolsTestmon": ".testmon",
        "FlextInfraProtocolsTransformers": ".transformers",
        "FlextInfraProtocolsValidate": ".validate",
        "FlextInfraProtocolsWorkspace": ".workspace",
        "FlextInfraProtocolsWorkspaceSnapshot": ".workspace_snapshot",
        "FlextInfraProtocolsWorktree": ".worktree",
    },
    public_exports=__all__,
)
