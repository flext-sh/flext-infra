"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods exposed directly via u.Infra.[method](...)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliUtilities

from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.cli import FlextInfraUtilitiesCli
from flext_infra._utilities.cst import FlextInfraUtilitiesCst
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra._utilities.github import FlextInfraUtilitiesGithub
from flext_infra._utilities.io import FlextInfraUtilitiesIo
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
from flext_infra._utilities.output import FlextInfraUtilitiesOutput
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra._utilities.paths import FlextInfraUtilitiesPaths
from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
from flext_infra._utilities.release import FlextInfraUtilitiesRelease
from flext_infra._utilities.reporting import FlextInfraUtilitiesReporting
from flext_infra._utilities.rope import FlextInfraUtilitiesRope
from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
from flext_infra._utilities.selection import FlextInfraUtilitiesSelection
from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess
from flext_infra._utilities.templates import FlextInfraUtilitiesTemplates
from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
from flext_infra._utilities.toml import FlextInfraUtilitiesToml
from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse
from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml
from flext_infra.codegen._utilities import FlextInfraUtilitiesCodegen
from flext_infra.refactor._utilities import FlextInfraUtilitiesRefactor
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)
from flext_infra.transformers._utilities_normalizer import (
    FlextInfraUtilitiesImportNormalizer,
)
from flext_infra.transformers.policy import FlextInfraRefactorTransformerPolicyUtilities


class FlextInfraUtilities(FlextCliUtilities):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import u

        u.Infra.git_run_checked(["status"])
        u.Infra.read_json(path)
        u.Infra.discover_projects(workspace_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraRefactorTransformerPolicyUtilities,
        FlextInfraUtilitiesCli,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCst,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesFormatting,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesIo,
        FlextInfraUtilitiesIteration,
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


FlextInfraUtilities.Infra.register_rope_post_hook(
    FlextInfraRefactorMigrateToClassMRO.run_as_hook,
)

u = FlextInfraUtilities
__all__ = ["FlextInfraUtilities", "u"]
