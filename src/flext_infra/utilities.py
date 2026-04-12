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
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesOutputReporting,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesPaths,
    FlextInfraUtilitiesPatterns,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesRope,
    FlextInfraUtilitiesSafety,
    FlextInfraUtilitiesToml,
    FlextInfraUtilitiesTomlParse,
    FlextInfraUtilitiesVersioning,
)
from flext_infra._utilities.deps_path_sync import (
    FlextInfraUtilitiesDependencyPathSync,
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
        FlextInfraUtilitiesReporting,
        FlextInfraUtilitiesOutputReporting,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesImportNormalizer,
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
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesDependencyPathSync,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPaths,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesToml,
        FlextInfraUtilitiesTomlParse,
        FlextInfraUtilitiesVersioning,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
