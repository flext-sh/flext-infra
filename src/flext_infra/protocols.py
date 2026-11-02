# AUTO-GENERATED FILE - Source bootstrap protocol facade.
"""Structural contracts projected from source model declarations."""

from __future__ import annotations

from flext_cli import FlextCliProtocols

from flext_infra._protocols import (
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
)
from flext_infra._protocols._codegen import (
    FlextInfraProtocolsCodegenFix,
    FlextInfraProtocolsCodegenLazyInit,
    FlextInfraProtocolsCodegenPipeline,
    FlextInfraProtocolsCodegenTransaction,
)
from flext_infra._protocols._config import FlextInfraProtocolsConfigWorkspace
from flext_infra._protocols._git import (
    FlextInfraProtocolsGitIdentity,
    FlextInfraProtocolsGitWorktreeFacts,
    FlextInfraProtocolsGitWorktreeState,
)
from flext_infra._protocols import FlextInfraProtocolsRopeMove
from flext_infra._protocols import FlextInfraProtocolsRopeRuntime
from flext_infra._protocols import FlextInfraProtocolsScan
from flext_infra._protocols import FlextInfraProtocolsSonarcloud
from flext_infra._protocols import FlextInfraProtocolsTransformers
from flext_infra._protocols import FlextInfraProtocolsValidate
from flext_infra._protocols import FlextInfraProtocolsWorkspace
from flext_infra._protocols.workspace_snapshot import (
    FlextInfraProtocolsWorkspaceSnapshot,
)
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
