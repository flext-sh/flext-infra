"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods exposed directly via u.Infra.[method](...)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import u

from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
from flext_infra._utilities.deps_path_sync import FlextInfraUtilitiesDependencyPathSync
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit
from flext_infra._utilities.docs_build import FlextInfraUtilitiesDocsBuild
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_fix import FlextInfraUtilitiesDocsFix
from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate
from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.docs_validate import FlextInfraUtilitiesDocsValidate
from flext_infra._utilities.engine import FlextInfraUtilitiesRefactorEngine
from flext_infra._utilities.github import FlextInfraUtilitiesGithub
from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
from flext_infra._utilities.mro_scan import FlextInfraUtilitiesRefactorMroScan
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.namespace_analysis import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
    FlextInfraUtilitiesRefactorNamespaceMro,
)
from flext_infra._utilities.namespace_facades import (
    FlextInfraUtilitiesRefactorNamespaceFacades,
)
from flext_infra._utilities.namespace_moves import (
    FlextInfraUtilitiesRefactorNamespaceMoves,
)
from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
from flext_infra._utilities.policy import FlextInfraUtilitiesRefactorPolicy
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
from flext_infra._utilities.release import FlextInfraUtilitiesRelease
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
from flext_infra._utilities.rope_module_patch import FlextInfraUtilitiesRopeModulePatch
from flext_infra._utilities.rope_mro_transform import (
    FlextInfraUtilitiesRopeMroTransform,
)
from flext_infra._utilities.rope_pep695_patch import (
    FlextInfraUtilitiesRopePep695Patch,
)
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
from flext_infra._utilities.scope_selector import FlextInfraUtilitiesScopeSelector
from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning


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
        FlextInfraUtilitiesRopePep695Patch,
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
        FlextInfraUtilitiesIteration,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesRefactorEngine,
        FlextInfraUtilitiesRefactorMroScan,
        FlextInfraUtilitiesRefactorNamespaceMro,
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceFacades,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesRefactorPolicy,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesRopeMroTransform,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesScopeSelector,
        FlextInfraUtilitiesVersioning,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
