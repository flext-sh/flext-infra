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
    FlextInfraUtilitiesRuleHelpers,
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


class FlextInfraUtilities(
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
    FlextInfraUtilitiesRuleHelpers,
    FlextInfraUtilitiesSafety,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
    FlextInfraUtilitiesTemplates,
    FlextInfraUtilitiesTerminal,
    FlextInfraUtilitiesToml,
    FlextInfraUtilitiesTomlParse,
    FlextInfraUtilitiesVersioning,
    FlextInfraUtilitiesYaml,
    FlextCliUtilities,
):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import u

        u.git_run_checked(["status"])
        u.read_json(path)
        u.discover_projects(workspace_root)
        u.parse_semver("1.2.3")
    """


u = FlextInfraUtilities
__all__ = ["FlextInfraUtilities", "u"]
