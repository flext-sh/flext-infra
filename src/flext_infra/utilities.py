"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods exposed directly via u.Infra.[method](...)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliUtilities
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCli,
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesOutput,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesPaths,
    FlextInfraUtilitiesPatterns,
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
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit
from flext_infra._utilities.docs_build import FlextInfraUtilitiesDocsBuild
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_fix import FlextInfraUtilitiesDocsFix
from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate
from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.docs_validate import FlextInfraUtilitiesDocsValidate
from flext_infra.codegen import FlextInfraUtilitiesCodegen
from flext_infra.refactor import FlextInfraUtilitiesRefactor
from flext_infra.transformers import (
    FlextInfraRefactorTransformerPolicyUtilities,
    FlextInfraUtilitiesImportNormalizer,
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
        FlextInfraUtilitiesCli,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraRefactorTransformerPolicyUtilities,
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
