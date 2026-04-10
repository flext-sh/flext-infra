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
    FlextInfraUtilitiesCli,
    FlextInfraUtilitiesCodegen,
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
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesOutputReporting,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesPaths,
    FlextInfraUtilitiesPatterns,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRefactorTransformerPolicy,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesRope,
    FlextInfraUtilitiesSafety,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesTerminal,
    FlextInfraUtilitiesToml,
    FlextInfraUtilitiesTomlParse,
    FlextInfraUtilitiesVersioning,
    FlextInfraUtilitiesYaml,
)


class FlextInfraUtilities(u):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import u

        u.Infra.git_run_checked(["status"])
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(workspace_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesReporting,
        FlextInfraUtilitiesOutputReporting,
        FlextInfraUtilitiesCli,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraUtilitiesRefactorTransformerPolicy,
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
        FlextInfraUtilitiesFormatting,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesDependencyPathSync,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPaths,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesSelection,
        FlextInfraUtilitiesTerminal,
        FlextInfraUtilitiesToml,
        FlextInfraUtilitiesTomlParse,
        FlextInfraUtilitiesVersioning,
        FlextInfraUtilitiesYaml,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities

__all__ = ["FlextInfraUtilities", "u"]
