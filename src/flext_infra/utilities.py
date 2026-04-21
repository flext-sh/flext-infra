"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods exposed directly via u.Infra.[method](...)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import u

from flext_infra import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegen,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCompatibility,
    FlextInfraUtilitiesDependencyPathSync,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsAudit,
    FlextInfraUtilitiesDocsBuild,
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsFix,
    FlextInfraUtilitiesDocsGenerate,
    FlextInfraUtilitiesDocsRender,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesDocsValidate,
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesGithubPr,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesPatterns,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRefactorCensus,
    FlextInfraUtilitiesRefactorEngine,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorNamespaceCommon,
    FlextInfraUtilitiesRefactorNamespaceFacades,
    FlextInfraUtilitiesRefactorNamespaceMoves,
    FlextInfraUtilitiesRefactorNamespaceMro,
    FlextInfraUtilitiesRefactorPolicy,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeAnalysisIntrospection,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeInventory,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesSafety,
    FlextInfraUtilitiesVersioning,
)


class FlextInfraUtilities(u):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import u

        u.Cli.run_checked(["git", "status"])
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(workspace_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCodegenNamespace,
        FlextInfraUtilitiesCompatibility,
        FlextInfraUtilitiesDependencyPathSync,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesRopeCore,
        FlextInfraUtilitiesRopeAnalysis,
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRopeHelpers,
        FlextInfraUtilitiesRopeInventory,
        FlextInfraUtilitiesRopeImports,
        FlextInfraUtilitiesRopeModulePatch,
        FlextInfraUtilitiesRopeSource,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesDocsApi,
        FlextInfraUtilitiesDocsAudit,
        FlextInfraUtilitiesDocsBuild,
        FlextInfraUtilitiesDocsContract,
        FlextInfraUtilitiesDocsFix,
        FlextInfraUtilitiesDocsGenerate,
        FlextInfraUtilitiesDocsRender,
        FlextInfraUtilitiesDocsScope,
        FlextInfraUtilitiesDocsValidate,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesGithubPr,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraUtilitiesIteration,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesRefactorEngine,
        FlextInfraUtilitiesRefactorMroScan,
        FlextInfraUtilitiesRefactorMroTransform,
        FlextInfraUtilitiesRefactorNamespaceMro,
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceFacades,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesRefactorPolicy,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesVersioning,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
