# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra._utilities.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra._utilities._docs_audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectorsMixin as FlextInfraUtilitiesDocsAuditDetectorsMixin,
    )
    from flext_infra._utilities._docs_scope_build import (
        FlextInfraUtilitiesDocsScopeBuildMixin as FlextInfraUtilitiesDocsScopeBuildMixin,
    )
    from flext_infra._utilities._docs_scope_selection import (
        FlextInfraUtilitiesDocsScopeSelectionMixin as FlextInfraUtilitiesDocsScopeSelectionMixin,
    )
    from flext_infra._utilities._github_pr_single import (
        FlextInfraUtilitiesGithubPrSingleMixin as FlextInfraUtilitiesGithubPrSingleMixin,
    )
    from flext_infra._utilities._github_sync import (
        FlextInfraUtilitiesGithubSyncMixin as FlextInfraUtilitiesGithubSyncMixin,
    )
    from flext_infra._utilities._project_discovery_candidates import (
        FlextInfraUtilitiesProjectDiscoveryCandidatesMixin as FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
    )
    from flext_infra._utilities._project_discovery_shape import (
        FlextInfraUtilitiesProjectDiscoveryShapeMixin as FlextInfraUtilitiesProjectDiscoveryShapeMixin,
    )
    from flext_infra._utilities._rope_bracket_balance import (
        FlextInfraUtilitiesRopeBracketBalanceMixin as FlextInfraUtilitiesRopeBracketBalanceMixin,
    )
    from flext_infra._utilities._rope_core_pymodule import (
        FlextInfraUtilitiesRopeCorePyModuleMixin as FlextInfraUtilitiesRopeCorePyModuleMixin,
    )
    from flext_infra._utilities._rope_core_resources import (
        FlextInfraUtilitiesRopeCoreResourcesMixin as FlextInfraUtilitiesRopeCoreResourcesMixin,
    )
    from flext_infra._utilities._rope_method_order import (
        FlextInfraUtilitiesRopeMethodOrderMixin as FlextInfraUtilitiesRopeMethodOrderMixin,
    )
    from flext_infra._utilities.base import (
        FlextInfraUtilitiesBase as FlextInfraUtilitiesBase,
    )
    from flext_infra._utilities.census import (
        FlextInfraUtilitiesRefactorCensus as FlextInfraUtilitiesRefactorCensus,
    )
    from flext_infra._utilities.codegen import (
        FlextInfraUtilitiesCodegen as FlextInfraUtilitiesCodegen,
    )
    from flext_infra._utilities.dependencies import (
        FlextInfraUtilitiesDependencies as FlextInfraUtilitiesDependencies,
    )
    from flext_infra._utilities.deps_repos import (
        FlextInfraInternalSyncRepoMixin as FlextInfraInternalSyncRepoMixin,
    )
    from flext_infra._utilities.discovery import (
        FlextInfraUtilitiesDiscovery as FlextInfraUtilitiesDiscovery,
    )
    from flext_infra._utilities.docs import (
        FlextInfraUtilitiesDocs as FlextInfraUtilitiesDocs,
    )
    from flext_infra._utilities.docs_api import (
        FlextInfraUtilitiesDocsApi as FlextInfraUtilitiesDocsApi,
    )
    from flext_infra._utilities.docs_audit import (
        FlextInfraUtilitiesDocsAudit as FlextInfraUtilitiesDocsAudit,
    )
    from flext_infra._utilities.docs_build import (
        FlextInfraUtilitiesDocsBuild as FlextInfraUtilitiesDocsBuild,
    )
    from flext_infra._utilities.docs_contract import (
        FlextInfraUtilitiesDocsContract as FlextInfraUtilitiesDocsContract,
    )
    from flext_infra._utilities.docs_fix import (
        FlextInfraUtilitiesDocsFix as FlextInfraUtilitiesDocsFix,
    )
    from flext_infra._utilities.docs_generate import (
        FlextInfraUtilitiesDocsGenerate as FlextInfraUtilitiesDocsGenerate,
    )
    from flext_infra._utilities.docs_render import (
        FlextInfraUtilitiesDocsRender as FlextInfraUtilitiesDocsRender,
    )
    from flext_infra._utilities.docs_scope import (
        FlextInfraUtilitiesDocsScope as FlextInfraUtilitiesDocsScope,
    )
    from flext_infra._utilities.docs_validate import (
        FlextInfraUtilitiesDocsValidate as FlextInfraUtilitiesDocsValidate,
    )
    from flext_infra._utilities.git_scope import (
        FlextInfraUtilitiesGitScope as FlextInfraUtilitiesGitScope,
    )
    from flext_infra._utilities.github import (
        FlextInfraUtilitiesGithub as FlextInfraUtilitiesGithub,
    )
    from flext_infra._utilities.github_pr import (
        FlextInfraUtilitiesGithubPr as FlextInfraUtilitiesGithubPr,
    )
    from flext_infra._utilities.log_parser import (
        FlextInfraUtilitiesLogParser as FlextInfraUtilitiesLogParser,
    )
    from flext_infra._utilities.mro_scan import (
        FlextInfraUtilitiesRefactorMroScan as FlextInfraUtilitiesRefactorMroScan,
    )
    from flext_infra._utilities.mro_scan_catalog import (
        FlextInfraUtilitiesMroScanCatalog as FlextInfraUtilitiesMroScanCatalog,
    )
    from flext_infra._utilities.mro_scan_source import (
        FlextInfraUtilitiesMroScanSource as FlextInfraUtilitiesMroScanSource,
    )
    from flext_infra._utilities.namespace import (
        FlextInfraUtilitiesCodegenNamespace as FlextInfraUtilitiesCodegenNamespace,
    )
    from flext_infra._utilities.namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceMro as FlextInfraUtilitiesRefactorNamespaceMro,
    )
    from flext_infra._utilities.namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon as FlextInfraUtilitiesRefactorNamespaceCommon,
    )
    from flext_infra._utilities.namespace_config import (
        FlextInfraUtilitiesNamespaceConfig as FlextInfraUtilitiesNamespaceConfig,
    )
    from flext_infra._utilities.namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades as FlextInfraUtilitiesRefactorNamespaceFacades,
    )
    from flext_infra._utilities.namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves as FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities.policy import (
        FlextInfraUtilitiesRefactorPolicy as FlextInfraUtilitiesRefactorPolicy,
    )
    from flext_infra._utilities.project_discovery import (
        FlextInfraUtilitiesProjectDiscovery as FlextInfraUtilitiesProjectDiscovery,
    )
    from flext_infra._utilities.protected_edit import (
        FlextInfraUtilitiesProtectedEdit as FlextInfraUtilitiesProtectedEdit,
    )
    from flext_infra._utilities.protected_edit_apply import (
        FlextInfraUtilitiesProtectedEditApply as FlextInfraUtilitiesProtectedEditApply,
    )
    from flext_infra._utilities.protected_edit_linting import (
        FlextInfraUtilitiesProtectedEditLinting as FlextInfraUtilitiesProtectedEditLinting,
    )
    from flext_infra._utilities.protected_edit_preview import (
        FlextInfraUtilitiesProtectedEditPreview as FlextInfraUtilitiesProtectedEditPreview,
    )
    from flext_infra._utilities.protected_edit_writes import (
        FlextInfraUtilitiesProtectedEditWrites as FlextInfraUtilitiesProtectedEditWrites,
    )
    from flext_infra._utilities.pyproject import (
        FlextInfraUtilitiesPyproject as FlextInfraUtilitiesPyproject,
    )
    from flext_infra._utilities.pyproject_conform import (
        FlextInfraUtilitiesPyprojectConform as FlextInfraUtilitiesPyprojectConform,
    )
    from flext_infra._utilities.refactor import (
        FlextInfraUtilitiesRefactor as FlextInfraUtilitiesRefactor,
    )
    from flext_infra._utilities.refactor_discovery import (
        FlextInfraUtilitiesRefactorDiscovery as FlextInfraUtilitiesRefactorDiscovery,
    )
    from flext_infra._utilities.release import (
        FlextInfraUtilitiesRelease as FlextInfraUtilitiesRelease,
    )
    from flext_infra._utilities.rope_analysis import (
        FlextInfraUtilitiesRopeAnalysis as FlextInfraUtilitiesRopeAnalysis,
    )
    from flext_infra._utilities.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection as FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities.rope_analysis_workspace import (
        FlextInfraUtilitiesRopeAnalysisWorkspace as FlextInfraUtilitiesRopeAnalysisWorkspace,
    )
    from flext_infra._utilities.rope_core import (
        FlextInfraUtilitiesRopeCore as FlextInfraUtilitiesRopeCore,
    )
    from flext_infra._utilities.rope_helpers import (
        FlextInfraUtilitiesRopeHelpers as FlextInfraUtilitiesRopeHelpers,
    )
    from flext_infra._utilities.rope_imports import (
        FlextInfraUtilitiesRopeImports as FlextInfraUtilitiesRopeImports,
    )
    from flext_infra._utilities.rope_inventory import (
        FlextInfraUtilitiesRopeInventory as FlextInfraUtilitiesRopeInventory,
    )
    from flext_infra._utilities.rope_module_patch import (
        FlextInfraUtilitiesRopeModulePatch as FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities.rope_mro_transform import (
        FlextInfraUtilitiesRopeMroTransform as FlextInfraUtilitiesRopeMroTransform,
    )
    from flext_infra._utilities.rope_pep695_patch import (
        FlextInfraUtilitiesRopePep695Patch as FlextInfraUtilitiesRopePep695Patch,
    )
    from flext_infra._utilities.rope_runtime import (
        FlextInfraUtilitiesRopeRuntime as FlextInfraUtilitiesRopeRuntime,
    )
    from flext_infra._utilities.rope_runtime_base import (
        FlextInfraUtilitiesRopeRuntimeBase as FlextInfraUtilitiesRopeRuntimeBase,
    )
    from flext_infra._utilities.rope_runtime_modules import (
        FlextInfraUtilitiesRopeRuntimeModules as FlextInfraUtilitiesRopeRuntimeModules,
    )
    from flext_infra._utilities.rope_runtime_refactors import (
        FlextInfraUtilitiesRopeRuntimeRefactors as FlextInfraUtilitiesRopeRuntimeRefactors,
    )
    from flext_infra._utilities.rope_runtime_types import (
        FlextInfraUtilitiesRopeRuntimeTypes as FlextInfraUtilitiesRopeRuntimeTypes,
    )
    from flext_infra._utilities.rope_source import (
        FlextInfraUtilitiesRopeSource as FlextInfraUtilitiesRopeSource,
    )
    from flext_infra._utilities.safety import (
        FlextInfraUtilitiesSafety as FlextInfraUtilitiesSafety,
    )
    from flext_infra._utilities.silent_failure_ast import (
        collect_silent_failure_findings as collect_silent_failure_findings,
        collect_silent_failure_fixes as collect_silent_failure_fixes,
    )
    from flext_infra._utilities.snapshot import (
        FlextInfraUtilitiesSnapshot as FlextInfraUtilitiesSnapshot,
    )
    from flext_infra._utilities.versioning import (
        FlextInfraUtilitiesVersioning as FlextInfraUtilitiesVersioning,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
