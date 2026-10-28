# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_cli import u as flext_cli_u

from flext_infra._utilities import (
    FlextInfraUtilitiesCodegen,
    FlextInfraUtilitiesCodemod,
    FlextInfraUtilitiesCompatibilityAliasValidation,
    FlextInfraUtilitiesDeferredSelfReferenceRewrite,
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesEnforcementCatalog,
    FlextInfraUtilitiesFacadeComponents,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesLazyInitLetters,
    FlextInfraUtilitiesLazyInitPlan,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesMiseBinary,
    FlextInfraUtilitiesNetwork,
    FlextInfraUtilitiesPrivateImportAncestry,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesPrivateImportValidation,
    FlextInfraUtilitiesProcess,
    FlextInfraUtilitiesPromoted,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesPyrefly,
    FlextInfraUtilitiesPytest,
    FlextInfraUtilitiesPytestCollection,
    FlextInfraUtilitiesPythonModel,
    FlextInfraUtilitiesQualifiedNames,
    FlextInfraUtilitiesRefactorCensus,
    FlextInfraUtilitiesRefactorNamespaceFlext,
    FlextInfraUtilitiesRefactorNamespaceMoves,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesResourceLimits,
    FlextInfraUtilitiesSemanticCutover,
    FlextInfraUtilitiesTransformerHeader,
    FlextInfraWorktreeLifecycle,
    FlextInfraWorktreeProvisioning,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeInventory,
    FlextInfraUtilitiesRopeNestedClassMove,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesInventory,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
    FlextInfraUtilitiesRopeSourceBindingCollector,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)


class FlextInfraUtilities(flext_cli_u):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import m, u

        u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=Path(".")))
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(repository_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCompatibilityAliasValidation,
        FlextInfraUtilitiesDeferredSelfReferenceRewrite,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesEnforcementCatalog,
        FlextInfraUtilitiesFacadeComponents,
        FlextInfraUtilitiesFacadeMembers,
        FlextInfraUtilitiesLazyInitLetters,
        FlextInfraUtilitiesLazyInitPlan,
        FlextInfraUtilitiesLazyInitRender,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesMiseBinary,
        FlextInfraUtilitiesRefactorNamespaceFlext,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesNetwork,
        FlextInfraUtilitiesPrivateImportAncestry,
        FlextInfraUtilitiesPrivateImportFacades,
        FlextInfraUtilitiesPrivateImportValidation,
        FlextInfraUtilitiesProcess,
        FlextInfraUtilitiesPromoted,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesPyrefly,
        FlextInfraUtilitiesPytestCollection,
        FlextInfraUtilitiesPythonModel,
        FlextInfraUtilitiesQualifiedNames,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesResourceLimits,
        FlextInfraUtilitiesSemanticCutover,
        FlextInfraUtilitiesTransformerHeader,
        FlextInfraWorktreeLifecycle,
        FlextInfraWorktreeProvisioning,
        FlextInfraUtilitiesRopeSourceBasesAliases,
        FlextInfraUtilitiesRopeSourceBasesInventory,
        FlextInfraUtilitiesRopeSourceBindingCollector,
        FlextInfraUtilitiesRopeSourceBasesRuntime,
        FlextInfraUtilitiesCodemod,
        FlextInfraUtilitiesPytest,
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRopeCore,
        FlextInfraUtilitiesRopeHelpers,
        FlextInfraUtilitiesRopeImports,
        FlextInfraUtilitiesRopeInventory,
        FlextInfraUtilitiesRopeNestedClassMove,
        FlextInfraUtilitiesRopeSource,
        FlextInfraUtilitiesRopeStructure,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities
__all__: list[str] = ["FlextInfraUtilities", "u"]
