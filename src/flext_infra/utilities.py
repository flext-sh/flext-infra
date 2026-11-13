# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliUtilities

from flext_infra._utilities import (
    FlextInfraUtilitiesCodegen,
    FlextInfraUtilitiesCodemod,
    FlextInfraUtilitiesCompatibilityAliasValidation,
    FlextInfraUtilitiesDeferredSelfReferenceRewrite,
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesEnforcementCatalog,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesGateAdmission,
    FlextInfraUtilitiesLazyInitLetters,
    FlextInfraUtilitiesLazyInitPlan,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesMiseBinary,
    FlextInfraUtilitiesModelsProtocolContracts,
    FlextInfraUtilitiesModelsProtocolRetirement,
    FlextInfraUtilitiesMypy,
    FlextInfraUtilitiesNetwork,
    FlextInfraUtilitiesPrivateImportAncestry,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesPrivateImportValidation,
    FlextInfraUtilitiesProcess,
    FlextInfraUtilitiesPromoted,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesProtocolPublication,
    FlextInfraUtilitiesPyrefly,
    FlextInfraUtilitiesPytest,
    FlextInfraUtilitiesPytestCollection,
    FlextInfraUtilitiesPythonModel,
    FlextInfraUtilitiesQualifiedNames,
    FlextInfraUtilitiesRefactorCensus,
    FlextInfraUtilitiesRefactorNamespaceFlext,
    FlextInfraUtilitiesRefactorNamespaceMoves,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesReleaseForge,
    FlextInfraUtilitiesResourceLimits,
    FlextInfraUtilitiesRope,
    FlextInfraUtilitiesSemanticCutover,
    FlextInfraUtilitiesTransformerHeader,
    FlextInfraWorktreeLifecycle,
    FlextInfraWorktreeProvisioning,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)


class FlextInfraUtilities(FlextCliUtilities):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import m, p, u

        u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=Path(".")))
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(repository_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCodemod,
        FlextInfraUtilitiesCompatibilityAliasValidation,
        FlextInfraUtilitiesDeferredSelfReferenceRewrite,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesEnforcementCatalog,
        FlextInfraUtilitiesFacadeMembers,
        FlextInfraUtilitiesGateAdmission,
        FlextInfraUtilitiesLazyInitLetters,
        FlextInfraUtilitiesLazyInitPlan,
        FlextInfraUtilitiesLazyInitRender,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesMiseBinary,
        FlextInfraUtilitiesMypy,
        FlextInfraUtilitiesRefactorNamespaceFlext,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesNetwork,
        FlextInfraUtilitiesPrivateImportAncestry,
        FlextInfraUtilitiesPrivateImportFacades,
        FlextInfraUtilitiesPrivateImportValidation,
        FlextInfraUtilitiesProcess,
        FlextInfraUtilitiesPromoted,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesModelsProtocolContracts,
        FlextInfraUtilitiesProtocolPublication,
        FlextInfraUtilitiesModelsProtocolRetirement,
        FlextInfraUtilitiesPyrefly,
        FlextInfraUtilitiesPytestCollection,
        FlextInfraUtilitiesPytest,
        FlextInfraUtilitiesPythonModel,
        FlextInfraUtilitiesQualifiedNames,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesReleaseForge,
        FlextInfraUtilitiesResourceLimits,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesSemanticCutover,
        FlextInfraUtilitiesTransformerHeader,
        FlextInfraWorktreeLifecycle,
        FlextInfraWorktreeProvisioning,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities
__all__: list[str] = ["FlextInfraUtilities", "u"]
