# AUTO-GENERATED FILE — Regenerate with: make gen
"""Structural contracts projected from source model declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TypeAlias

from flext_cli import FlextCliProtocols

from flext_infra._protocols import (
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
    FlextInfraProtocolsDepsToolConfigProjectMise,
    FlextInfraProtocolsDepsToolConfigTypeCheckers,
    FlextInfraProtocolsDocs,
    FlextInfraProtocolsDocsCollection,
    FlextInfraProtocolsDocsGeneration,
    FlextInfraProtocolsDuplication,
    FlextInfraProtocolsEnforcementCatalog,
    FlextInfraProtocolsGates,
    FlextInfraProtocolsGit,
    FlextInfraProtocolsLayout,
    FlextInfraProtocolsMiseToolchain,
    FlextInfraProtocolsMiseToolchainBase,
    FlextInfraProtocolsMiseToolchainRepair,
    FlextInfraProtocolsMixins,
    FlextInfraProtocolsProjectArtifacts,
    FlextInfraProtocolsProjectGitignore,
    FlextInfraProtocolsPromoted,
    FlextInfraProtocolsRefactor,
    FlextInfraProtocolsRefactorAstGrep,
    FlextInfraProtocolsRefactorNamespaceEnforcer,
    FlextInfraProtocolsRelease,
    FlextInfraProtocolsReleaseForge,
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
)


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
        FlextInfraProtocolsDepsToolConfigProjectMise,
        FlextInfraProtocolsDepsToolConfigTypeCheckers,
        FlextInfraProtocolsDocs,
        FlextInfraProtocolsDocsCollection,
        FlextInfraProtocolsDocsGeneration,
        FlextInfraProtocolsDuplication,
        FlextInfraProtocolsEnforcementCatalog,
        FlextInfraProtocolsGates,
        FlextInfraProtocolsGit,
        FlextInfraProtocolsLayout,
        FlextInfraProtocolsMiseToolchain,
        FlextInfraProtocolsMiseToolchainBase,
        FlextInfraProtocolsMiseToolchainRepair,
        FlextInfraProtocolsMixins,
        FlextInfraProtocolsProjectArtifacts,
        FlextInfraProtocolsProjectGitignore,
        FlextInfraProtocolsPromoted,
        FlextInfraProtocolsRefactor,
        FlextInfraProtocolsRefactorAstGrep,
        FlextInfraProtocolsRefactorNamespaceEnforcer,
        FlextInfraProtocolsRelease,
        FlextInfraProtocolsReleaseForge,
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

        NativeStorageSlot: TypeAlias = FlextInfraProtocolsCheck.NativeStorageSlot
        RopeWildcard: TypeAlias = FlextInfraProtocolsRopeRuntime.RopeWildcard
        ModScanCounts: TypeAlias = FlextInfraProtocolsScan.ModScanCounts
        ModOccurrenceReport: TypeAlias = FlextInfraProtocolsScan.ModOccurrenceReport


p = FlextInfraProtocols
__all__: list[str] = ["FlextInfraProtocols", "p"]
