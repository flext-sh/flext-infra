# AUTO-GENERATED FILE - Source bootstrap protocol facade.
"""Structural contracts projected from source model declarations."""

from __future__ import annotations

from flext_cli import FlextCliProtocols
from flext_infra._protocols._codegen.fix import FlextInfraProtocolsCodegenFix
from flext_infra._protocols._codegen.lazy_init import FlextInfraProtocolsCodegenLazyInit
from flext_infra._protocols._codegen.pipeline import FlextInfraProtocolsCodegenPipeline
from flext_infra._protocols._codegen.transaction import FlextInfraProtocolsCodegenTransaction
from flext_infra._protocols._config.workspace import FlextInfraProtocolsConfigWorkspace
from flext_infra._protocols._git.identity import FlextInfraProtocolsGitIdentity
from flext_infra._protocols._git.worktree_facts import FlextInfraProtocolsGitWorktreeFacts
from flext_infra._protocols._git.worktree_state import FlextInfraProtocolsGitWorktreeState
from flext_infra._protocols.base import FlextInfraProtocolsBase
from flext_infra._protocols.census import FlextInfraProtocolsCensus
from flext_infra._protocols.check import FlextInfraProtocolsCheck
from flext_infra._protocols.codegen_render import FlextInfraProtocolsCodegenRender
from flext_infra._protocols.codemod import FlextInfraProtocolsCodemod
from flext_infra._protocols.deps import FlextInfraProtocolsDeps
from flext_infra._protocols.deps_toml import FlextInfraProtocolsDepsToml
from flext_infra._protocols.deps_tool_config import FlextInfraProtocolsDepsToolConfig
from flext_infra._protocols.deps_tool_config_linters import FlextInfraProtocolsDepsToolConfigLinters
from flext_infra._protocols.deps_tool_config_type_checkers import FlextInfraProtocolsDepsToolConfigTypeCheckers
from flext_infra._protocols.docs import FlextInfraProtocolsDocs
from flext_infra._protocols.docs_collection import FlextInfraProtocolsDocsCollection
from flext_infra._protocols.docs_generation import FlextInfraProtocolsDocsGeneration
from flext_infra._protocols.duplication import FlextInfraProtocolsDuplication
from flext_infra._protocols.gates import FlextInfraProtocolsGates
from flext_infra._protocols.git import FlextInfraProtocolsGit
from flext_infra._protocols.git_lane_inputs import FlextInfraProtocolsGitLaneInputs
from flext_infra._protocols.mise_toolchain_base import FlextInfraProtocolsMiseToolchainBase
from flext_infra._protocols.mixins import FlextInfraProtocolsMixins
from flext_infra._protocols.promoted import FlextInfraProtocolsPromoted
from flext_infra._protocols.refactor import FlextInfraProtocolsRefactor
from flext_infra._protocols.refactor_ast_grep import FlextInfraProtocolsRefactorAstGrep
from flext_infra._protocols.refactor_namespace_enforcer import FlextInfraProtocolsRefactorNamespaceEnforcer
from flext_infra._protocols.rope import FlextInfraProtocolsRope
from flext_infra._protocols.rope_move import FlextInfraProtocolsRopeMove
from flext_infra._protocols.rope_runtime import FlextInfraProtocolsRopeRuntime
from flext_infra._protocols.scan import FlextInfraProtocolsScan
from flext_infra._protocols.sonarcloud import FlextInfraProtocolsSonarcloud
from flext_infra._protocols.transformers import FlextInfraProtocolsTransformers
from flext_infra._protocols.validate import FlextInfraProtocolsValidate
from flext_infra._protocols.workspace import FlextInfraProtocolsWorkspace
from flext_infra._protocols.workspace_snapshot import FlextInfraProtocolsWorkspaceSnapshot
from flext_infra._protocols.worktree import FlextInfraProtocolsWorktree


class FlextInfraProtocols(FlextCliProtocols):
    """Structural contracts for flext-infra."""

    class Infra(
        FlextInfraProtocolsCodegenFix,
        FlextInfraProtocolsCodegenLazyInit,
        FlextInfraProtocolsCodegenPipeline,
        FlextInfraProtocolsCodegenTransaction,
        FlextInfraProtocolsConfigWorkspace,
        FlextInfraProtocolsGitIdentity,
        FlextInfraProtocolsGitWorktreeFacts,
        FlextInfraProtocolsGitWorktreeState,
        FlextInfraProtocolsBase,
        FlextInfraProtocolsCensus,
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsCodegenRender,
        FlextInfraProtocolsCodemod,
        FlextInfraProtocolsDeps,
        FlextInfraProtocolsDepsToml,
        FlextInfraProtocolsDepsToolConfig,
        FlextInfraProtocolsDepsToolConfigLinters,
        FlextInfraProtocolsDepsToolConfigTypeCheckers,
        FlextInfraProtocolsDocs,
        FlextInfraProtocolsDocsCollection,
        FlextInfraProtocolsDocsGeneration,
        FlextInfraProtocolsDuplication,
        FlextInfraProtocolsGates,
        FlextInfraProtocolsGit,
        FlextInfraProtocolsGitLaneInputs,
        FlextInfraProtocolsMiseToolchainBase,
        FlextInfraProtocolsMixins,
        FlextInfraProtocolsPromoted,
        FlextInfraProtocolsRefactor,
        FlextInfraProtocolsRefactorAstGrep,
        FlextInfraProtocolsRefactorNamespaceEnforcer,
        FlextInfraProtocolsRope,
        FlextInfraProtocolsRopeMove,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsScan,
        FlextInfraProtocolsSonarcloud,
        FlextInfraProtocolsTransformers,
        FlextInfraProtocolsValidate,
        FlextInfraProtocolsWorkspace,
        FlextInfraProtocolsWorkspaceSnapshot,
        FlextInfraProtocolsWorktree,
    ):
        """Aggregate source-derived protocol contracts."""

p = FlextInfraProtocols
__all__: list[str] = ["FlextInfraProtocols", "p"]
