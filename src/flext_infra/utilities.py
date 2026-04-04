"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods exposed directly via u.Infra.[method](...)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliUtilities
from flext_infra import (
    FlextInfraRefactorTransformerPolicyUtilities,
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCli,
    FlextInfraUtilitiesCodegen,
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesOutput,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesPaths,
    FlextInfraUtilitiesPatterns,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesRope,
    FlextInfraUtilitiesSafety,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
    FlextInfraUtilitiesTemplates,
    FlextInfraUtilitiesTerminal,
    FlextInfraUtilitiesToml,
    FlextInfraUtilitiesTomlParse,
    FlextInfraUtilitiesVersioning,
    FlextInfraUtilitiesYaml,
)


class FlextInfraUtilities(FlextCliUtilities):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import u

        u.Infra.git_run_checked(["status"])
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(workspace_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraRefactorTransformerPolicyUtilities,
        FlextInfraUtilitiesCli,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesFormatting,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesIo,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesOutput,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPaths,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesReporting,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesSelection,
        FlextInfraUtilitiesSubprocess,
        FlextInfraUtilitiesTemplates,
        FlextInfraUtilitiesTerminal,
        FlextInfraUtilitiesToml,
        FlextInfraUtilitiesTomlParse,
        FlextInfraUtilitiesVersioning,
        FlextInfraUtilitiesYaml,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities
__all__ = ["FlextInfraUtilities", "u"]
