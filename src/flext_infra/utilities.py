# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
from flext_infra._utilities._rope._analysis.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities._rope.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities._rope.rope_inventory import FlextInfraUtilitiesRopeInventory
from flext_infra._utilities._rope.rope_nested_class_move import (
    FlextInfraUtilitiesRopeNestedClassMove,
)
from flext_infra._utilities._rope.rope_source import FlextInfraUtilitiesRopeSource
from flext_infra._utilities._rope.rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._rope.rope_structure import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities._rope.source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope.source_bases_inventory import (
    FlextInfraUtilitiesRopeSourceBasesInventory,
)
from flext_infra._utilities._rope.source_bases_inventory_collector import (
    FlextInfraUtilitiesRopeSourceBindingCollector,
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
