# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
    from flext_infra._utilities.codegen_facade_syntax import (
        FlextInfraUtilitiesCodegenFacadeSyntax,
    )
    from flext_infra._utilities.codegen_facades import FlextInfraUtilitiesCodegenFacades
    from flext_infra._utilities.codegen_file_plan import (
        FlextInfraUtilitiesCodegenFilePlan,
    )
    from flext_infra._utilities.codemod import FlextInfraUtilitiesCodemod
    from flext_infra._utilities.compatibility_alias_validation import (
        FlextInfraUtilitiesCompatibilityAliasValidation,
    )
    from flext_infra._utilities.deferred_self_reference_rewrite import (
        FlextInfraUtilitiesDeferredSelfReferenceRewrite,
    )
    from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
    from flext_infra._utilities.dependency import FlextInfraUtilitiesDependency
    from flext_infra._utilities.dependency_requirements import (
        FlextInfraUtilitiesDependencyRequirements,
    )
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
    from flext_infra._utilities.enforcement_catalog import (
        FlextInfraUtilitiesEnforcementCatalog,
    )
    from flext_infra._utilities.facade_components import (
        FlextInfraUtilitiesFacadeComponents,
    )
    from flext_infra._utilities.facade_members import FlextInfraUtilitiesFacadeMembers
    from flext_infra._utilities.git import FlextInfraUtilitiesGit
    from flext_infra._utilities.import_law import FlextInfraUtilitiesImportLaw
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.iteration_directory import (
        FlextInfraUtilitiesIterationDirectory,
    )
    from flext_infra._utilities.iteration_matching import (
        FlextInfraUtilitiesIterationMatching,
    )
    from flext_infra._utilities.iteration_workspace import (
        FlextInfraUtilitiesIterationWorkspace,
    )
    from flext_infra._utilities.lazy_init_letters import (
        FlextInfraUtilitiesLazyInitLetters,
    )
    from flext_infra._utilities.lazy_init_plan import FlextInfraUtilitiesLazyInitPlan
    from flext_infra._utilities.lazy_init_render import (
        FlextInfraUtilitiesLazyInitRender,
    )
    from flext_infra._utilities.lint_recipes import FlextInfraUtilitiesLintRecipes
    from flext_infra._utilities.lint_source_positions import (
        FlextInfraUtilitiesLintSourcePositions,
    )
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.managed_conflicts import (
        FlextInfraUtilitiesManagedConflicts,
    )
    from flext_infra._utilities.mise_binary import FlextInfraUtilitiesMiseBinary
    from flext_infra._utilities.mypy import FlextInfraUtilitiesMypy
    from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
    from flext_infra._utilities.namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceFlext,
    )
    from flext_infra._utilities.namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
    )
    from flext_infra._utilities.namespace_config import (
        FlextInfraUtilitiesNamespaceConfig,
    )
    from flext_infra._utilities.namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities.native_tooling import FlextInfraUtilitiesNativeTooling
    from flext_infra._utilities.network import FlextInfraUtilitiesNetwork
    from flext_infra._utilities.private_import_ancestry import (
        FlextInfraUtilitiesPrivateImportAncestry,
    )
    from flext_infra._utilities.private_import_facades import (
        FlextInfraUtilitiesPrivateImportFacades,
    )
    from flext_infra._utilities.private_import_validation import (
        FlextInfraUtilitiesPrivateImportValidation,
    )
    from flext_infra._utilities.process import FlextInfraUtilitiesProcess
    from flext_infra._utilities.project import FlextInfraUtilitiesProject
    from flext_infra._utilities.project_discovery import (
        FlextInfraUtilitiesProjectDiscovery,
    )
    from flext_infra._utilities.project_managed_artifacts import (
        FlextInfraUtilitiesProjectManagedArtifacts,
    )
    from flext_infra._utilities.promoted import FlextInfraUtilitiesPromoted
    from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
    from flext_infra._utilities.protected_edit_apply import (
        FlextInfraUtilitiesProtectedEditApply,
    )
    from flext_infra._utilities.protected_edit_linting import (
        FlextInfraUtilitiesProtectedEditLinting,
    )
    from flext_infra._utilities.protected_edit_preview import (
        FlextInfraUtilitiesProtectedEditPreview,
    )
    from flext_infra._utilities.protected_edit_writes import (
        FlextInfraUtilitiesProtectedEditWrites,
    )
    from flext_infra._utilities.protocol_models import FlextInfraModelsUtilitiesProtocol
    from flext_infra._utilities.pyrefly import FlextInfraUtilitiesPyrefly
    from flext_infra._utilities.pytest_collection import (
        FlextInfraUtilitiesPytestCollection,
    )
    from flext_infra._utilities.pytest_surface import FlextInfraUtilitiesPytest
    from flext_infra._utilities.python_model import FlextInfraUtilitiesPythonModel
    from flext_infra._utilities.qualified_names import FlextInfraUtilitiesQualifiedNames
    from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease
    from flext_infra._utilities.repository import FlextInfraUtilitiesRepository
    from flext_infra._utilities.resource_limits import FlextInfraUtilitiesResourceLimits
    from flext_infra._utilities.semantic_cutover import (
        FlextInfraUtilitiesSemanticCutover,
    )
    from flext_infra._utilities.transformer_header import (
        FlextInfraUtilitiesTransformerHeader,
    )
    from flext_infra._utilities.transformer_header_parser import (
        FlextInfraUtilitiesTransformerHeaderParser,
    )
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra._utilities.workspace_inventory import (
        FlextInfraUtilitiesWorkspaceInventory,
    )
    from flext_infra._utilities.workspace_manifest import (
        FlextInfraUtilitiesWorkspaceManifest,
    )
    from flext_infra._utilities.workspace_snapshot import (
        FlextInfraUtilitiesWorkspaceSnapshot,
    )
    from flext_infra._utilities.worktree_lifecycle import FlextInfraWorktreeLifecycle
    from flext_infra._utilities.worktree_provisioning import (
        FlextInfraWorktreeProvisioning,
    )


__all__: tuple[str, ...] = (
    "FlextInfraModelsUtilitiesProtocol",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenFacadeSyntax",
    "FlextInfraUtilitiesCodegenFacades",
    "FlextInfraUtilitiesCodegenFilePlan",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesCodemod",
    "FlextInfraUtilitiesCompatibilityAliasValidation",
    "FlextInfraUtilitiesDeferredSelfReferenceRewrite",
    "FlextInfraUtilitiesDependencies",
    "FlextInfraUtilitiesDependency",
    "FlextInfraUtilitiesDependencyRequirements",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesEnforcementCatalog",
    "FlextInfraUtilitiesFacadeComponents",
    "FlextInfraUtilitiesFacadeMembers",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesImportLaw",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesIterationDirectory",
    "FlextInfraUtilitiesIterationMatching",
    "FlextInfraUtilitiesIterationWorkspace",
    "FlextInfraUtilitiesLazyInitLetters",
    "FlextInfraUtilitiesLazyInitPlan",
    "FlextInfraUtilitiesLazyInitRender",
    "FlextInfraUtilitiesLintRecipes",
    "FlextInfraUtilitiesLintSourcePositions",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesManagedConflicts",
    "FlextInfraUtilitiesMiseBinary",
    "FlextInfraUtilitiesMypy",
    "FlextInfraUtilitiesNamespaceConfig",
    "FlextInfraUtilitiesNativeTooling",
    "FlextInfraUtilitiesNetwork",
    "FlextInfraUtilitiesPrivateImportAncestry",
    "FlextInfraUtilitiesPrivateImportFacades",
    "FlextInfraUtilitiesPrivateImportValidation",
    "FlextInfraUtilitiesProcess",
    "FlextInfraUtilitiesProject",
    "FlextInfraUtilitiesProjectDiscovery",
    "FlextInfraUtilitiesProjectManagedArtifacts",
    "FlextInfraUtilitiesPromoted",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesProtectedEditApply",
    "FlextInfraUtilitiesProtectedEditLinting",
    "FlextInfraUtilitiesProtectedEditPreview",
    "FlextInfraUtilitiesProtectedEditWrites",
    "FlextInfraUtilitiesPyrefly",
    "FlextInfraUtilitiesPytest",
    "FlextInfraUtilitiesPytestCollection",
    "FlextInfraUtilitiesPythonModel",
    "FlextInfraUtilitiesQualifiedNames",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceFlext",
    "FlextInfraUtilitiesRefactorNamespaceMoves",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesRepository",
    "FlextInfraUtilitiesResourceLimits",
    "FlextInfraUtilitiesSemanticCutover",
    "FlextInfraUtilitiesTransformerHeader",
    "FlextInfraUtilitiesTransformerHeaderParser",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesWorkspaceInventory",
    "FlextInfraUtilitiesWorkspaceManifest",
    "FlextInfraUtilitiesWorkspaceSnapshot",
    "FlextInfraWorktreeLifecycle",
    "FlextInfraWorktreeProvisioning",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesBase": ".base",
        "FlextInfraUtilitiesCodegen": ".codegen",
        "FlextInfraUtilitiesCodegenFacadeSyntax": ".codegen_facade_syntax",
        "FlextInfraUtilitiesCodegenFacades": ".codegen_facades",
        "FlextInfraUtilitiesCodegenFilePlan": ".codegen_file_plan",
        "FlextInfraUtilitiesCodegenNamespace": ".namespace",
        "FlextInfraUtilitiesCodemod": ".codemod",
        "FlextInfraUtilitiesCompatibilityAliasValidation": (
            ".compatibility_alias_validation"
        ),
        "FlextInfraUtilitiesDeferredSelfReferenceRewrite": (
            ".deferred_self_reference_rewrite"
        ),
        "FlextInfraUtilitiesDependencies": ".dependencies",
        "FlextInfraUtilitiesDependency": ".dependency",
        "FlextInfraUtilitiesDependencyRequirements": ".dependency_requirements",
        "FlextInfraUtilitiesDiscovery": ".discovery",
        "FlextInfraUtilitiesDocs": ".docs",
        "FlextInfraUtilitiesEnforcementCatalog": ".enforcement_catalog",
        "FlextInfraUtilitiesFacadeComponents": ".facade_components",
        "FlextInfraUtilitiesFacadeMembers": ".facade_members",
        "FlextInfraUtilitiesGit": ".git",
        "FlextInfraUtilitiesImportLaw": ".import_law",
        "FlextInfraUtilitiesIteration": ".iteration",
        "FlextInfraUtilitiesIterationDirectory": ".iteration_directory",
        "FlextInfraUtilitiesIterationMatching": ".iteration_matching",
        "FlextInfraUtilitiesIterationWorkspace": ".iteration_workspace",
        "FlextInfraUtilitiesLazyInitLetters": ".lazy_init_letters",
        "FlextInfraUtilitiesLazyInitPlan": ".lazy_init_plan",
        "FlextInfraUtilitiesLazyInitRender": ".lazy_init_render",
        "FlextInfraUtilitiesLintRecipes": ".lint_recipes",
        "FlextInfraUtilitiesLintSourcePositions": ".lint_source_positions",
        "FlextInfraUtilitiesLogParser": ".log_parser",
        "FlextInfraUtilitiesManagedConflicts": ".managed_conflicts",
        "FlextInfraUtilitiesMiseBinary": ".mise_binary",
        "FlextInfraUtilitiesMypy": ".mypy",
        "FlextInfraUtilitiesNamespaceConfig": ".namespace_config",
        "FlextInfraUtilitiesNativeTooling": ".native_tooling",
        "FlextInfraUtilitiesNetwork": ".network",
        "FlextInfraUtilitiesPrivateImportAncestry": ".private_import_ancestry",
        "FlextInfraUtilitiesPrivateImportFacades": ".private_import_facades",
        "FlextInfraUtilitiesPrivateImportValidation": ".private_import_validation",
        "FlextInfraUtilitiesProcess": ".process",
        "FlextInfraUtilitiesProject": ".project",
        "FlextInfraUtilitiesProjectDiscovery": ".project_discovery",
        "FlextInfraUtilitiesProjectManagedArtifacts": ".project_managed_artifacts",
        "FlextInfraUtilitiesPromoted": ".promoted",
        "FlextInfraUtilitiesProtectedEdit": ".protected_edit",
        "FlextInfraUtilitiesProtectedEditApply": ".protected_edit_apply",
        "FlextInfraUtilitiesProtectedEditLinting": ".protected_edit_linting",
        "FlextInfraUtilitiesProtectedEditPreview": ".protected_edit_preview",
        "FlextInfraUtilitiesProtectedEditWrites": ".protected_edit_writes",
        "FlextInfraModelsUtilitiesProtocol": ".protocol_models",
        "FlextInfraUtilitiesPyrefly": ".pyrefly",
        "FlextInfraUtilitiesPytest": ".pytest_surface",
        "FlextInfraUtilitiesPytestCollection": ".pytest_collection",
        "FlextInfraUtilitiesPythonModel": ".python_model",
        "FlextInfraUtilitiesQualifiedNames": ".qualified_names",
        "FlextInfraUtilitiesRefactor": ".refactor",
        "FlextInfraUtilitiesRefactorCensus": ".census",
        "FlextInfraUtilitiesRefactorNamespaceCommon": ".namespace_common",
        "FlextInfraUtilitiesRefactorNamespaceFlext": ".namespace_analysis",
        "FlextInfraUtilitiesRefactorNamespaceMoves": ".namespace_moves",
        "FlextInfraUtilitiesRelease": ".release",
        "FlextInfraUtilitiesRepository": ".repository",
        "FlextInfraUtilitiesResourceLimits": ".resource_limits",
        "FlextInfraUtilitiesSemanticCutover": ".semantic_cutover",
        "FlextInfraUtilitiesTransformerHeader": ".transformer_header",
        "FlextInfraUtilitiesTransformerHeaderParser": ".transformer_header_parser",
        "FlextInfraUtilitiesVersioning": ".versioning",
        "FlextInfraUtilitiesWorkspaceInventory": ".workspace_inventory",
        "FlextInfraUtilitiesWorkspaceManifest": ".workspace_manifest",
        "FlextInfraUtilitiesWorkspaceSnapshot": ".workspace_snapshot",
        "FlextInfraWorktreeLifecycle": ".worktree_lifecycle",
        "FlextInfraWorktreeProvisioning": ".worktree_provisioning",
    }),
    public_exports=__all__,
)
