# AUTO-GENERATED FILE — Regenerate with: make gen
"""utilities package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._codemod.codemod_binding_chain import (
        FlextInfraUtilitiesCodemodBindingChain,
    )
    from flext_infra._utilities._codemod.codemod_import_law_rules import (
        FlextInfraUtilitiesCodemodImportLawRules,
    )
    from flext_infra._utilities._codemod.codemod_native_cascade import (
        FlextInfraUtilitiesCodemodNativeCascade,
    )
    from flext_infra._utilities._codemod.codemod_native_package_utilities import (
        FlextInfraUtilitiesCodemodNativePackageUtilities,
    )
    from flext_infra._utilities._codemod.codemod_native_utilities import (
        FlextInfraUtilitiesCodemodNativeUtilities,
    )
    from flext_infra._utilities._codemod.codemod_project import (
        FlextInfraUtilitiesCodemodProject,
    )
    from flext_infra._utilities._codemod.codemod_project_facts import (
        FlextInfraUtilitiesCodemodProjectFacts,
    )
    from flext_infra._utilities._codemod.codemod_rules import (
        FlextInfraUtilitiesCodemodRules,
    )
    from flext_infra._utilities._codemod.codemod_scopes import (
        FlextInfraUtilitiesCodemodScopes,
    )
    from flext_infra._utilities._codemod.codemod_type_set_rules import (
        FlextInfraUtilitiesCodemodTypeSetRules,
    )
    from flext_infra._utilities._codemod.rules_distributions import (
        FlextInfraUtilitiesCodemodRulesDistributions,
    )
    from flext_infra._utilities._dependency.deptry import (
        FlextInfraUtilitiesDependencyDeptry,
    )
    from flext_infra._utilities._docs.audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectors,
    )
    from flext_infra._utilities._docs.command_contract import (
        FlextInfraUtilitiesDocsCommandContract,
    )
    from flext_infra._utilities._docs.docs_api import FlextInfraUtilitiesDocsApi
    from flext_infra._utilities._docs.docs_audit import FlextInfraUtilitiesDocsAudit
    from flext_infra._utilities._docs.docs_build import FlextInfraUtilitiesDocsBuild
    from flext_infra._utilities._docs.docs_collection import (
        FlextInfraUtilitiesDocsCollection,
    )
    from flext_infra._utilities._docs.docs_collection_sources import (
        FlextInfraUtilitiesDocsCollectionSources,
    )
    from flext_infra._utilities._docs.docs_contract import (
        FlextInfraUtilitiesDocsContract,
    )
    from flext_infra._utilities._docs.docs_fix import FlextInfraUtilitiesDocsFix
    from flext_infra._utilities._docs.docs_generate import (
        FlextInfraUtilitiesDocsGenerate,
    )
    from flext_infra._utilities._docs.docs_render import FlextInfraUtilitiesDocsRender
    from flext_infra._utilities._docs.docs_scope import FlextInfraUtilitiesDocsScope
    from flext_infra._utilities._docs.docs_scope_projects import (
        FlextInfraUtilitiesDocsScopeProjectsMixin,
    )
    from flext_infra._utilities._docs.docs_validate import (
        FlextInfraUtilitiesDocsValidate,
    )
    from flext_infra._utilities._docs.generate_plan import (
        FlextInfraUtilitiesDocsGeneratePlan,
    )
    from flext_infra._utilities._docs.generate_project import (
        FlextInfraUtilitiesDocsGenerateProject,
    )
    from flext_infra._utilities._docs.generate_root import (
        FlextInfraUtilitiesDocsGenerateRoot,
    )
    from flext_infra._utilities._docs.generate_sources import (
        FlextInfraUtilitiesDocsGenerateSources,
    )
    from flext_infra._utilities._docs.github_links import (
        FlextInfraUtilitiesDocsGithubLinks,
    )
    from flext_infra._utilities._docs.guides import FlextInfraUtilitiesDocsGuides
    from flext_infra._utilities._docs.scope_build import (
        FlextInfraUtilitiesDocsScopeBuild,
    )
    from flext_infra._utilities._docs.scope_paths import (
        FlextInfraUtilitiesDocsScopePaths,
    )
    from flext_infra._utilities._docs.scope_policy import (
        FlextInfraUtilitiesDocsScopePolicy,
    )
    from flext_infra._utilities._docs.scope_selection import (
        FlextInfraUtilitiesDocsScopeSelection,
    )
    from flext_infra._utilities._docs.scope_state import (
        FlextInfraUtilitiesDocsScopeState,
    )
    from flext_infra._utilities._git.attestation import (
        FlextInfraUtilitiesGitAttestationMixin,
    )
    from flext_infra._utilities._git.attestation_evidence import (
        FlextInfraUtilitiesGitAttestationEvidenceMixin,
    )
    from flext_infra._utilities._git.gitignore import FlextInfraUtilitiesGitignore
    from flext_infra._utilities._git.lane_hygiene import (
        FlextInfraUtilitiesGitLaneHygieneMixin,
    )
    from flext_infra._utilities._git.mutation_scope import (
        FlextInfraUtilitiesGitMutationScopeMixin,
    )
    from flext_infra._utilities._git.remote import FlextInfraUtilitiesGitRemote
    from flext_infra._utilities._git.repo import FlextInfraUtilitiesGitRepo
    from flext_infra._utilities._git.requirement_source import (
        FlextInfraUtilitiesGitRequirementSource,
    )
    from flext_infra._utilities._git.scope import FlextInfraUtilitiesGitScopeMixin
    from flext_infra._utilities._git.semantic_identity import (
        FlextInfraUtilitiesGitSemanticIdentityMixin,
    )
    from flext_infra._utilities._git.semantic_index import (
        FlextInfraUtilitiesGitSemanticIndexMixin,
    )
    from flext_infra._utilities._git.semantic_lane import (
        FlextInfraUtilitiesGitSemanticLaneMixin,
    )
    from flext_infra._utilities._git.semantic_paths import (
        FlextInfraUtilitiesGitSemanticPathsMixin,
    )
    from flext_infra._utilities._git.semantic_publish import (
        FlextInfraUtilitiesGitSemanticPublishMixin,
    )
    from flext_infra._utilities._git.semantic_refs import (
        FlextInfraUtilitiesGitSemanticRefsMixin,
    )
    from flext_infra._utilities._git.semantic_submodule import (
        FlextInfraUtilitiesGitSemanticSubmoduleMixin,
    )
    from flext_infra._utilities._git.semantic_worktree import (
        FlextInfraUtilitiesGitSemanticWorktreeMixin,
    )
    from flext_infra._utilities._git.state_capture import (
        FlextInfraUtilitiesGitStateCaptureMixin,
    )
    from flext_infra._utilities._git.state_checkpoint import (
        FlextInfraUtilitiesGitStateCheckpointMixin,
    )
    from flext_infra._utilities._git.state_files import (
        FlextInfraUtilitiesGitStateFilesMixin,
    )
    from flext_infra._utilities._git.state_publication import (
        FlextInfraUtilitiesGitStatePublicationMixin,
    )
    from flext_infra._utilities._git.state_snapshot import (
        FlextInfraUtilitiesGitStateSnapshotMixin,
    )
    from flext_infra._utilities._git.state_transition import (
        FlextInfraUtilitiesGitStateTransitionMixin,
    )
    from flext_infra._utilities._git.state_trees import (
        FlextInfraUtilitiesGitStateTreesMixin,
    )
    from flext_infra._utilities._git.worktree import FlextInfraUtilitiesGitWorktreeMixin
    from flext_infra._utilities._git.worktree_checkpoint import (
        FlextInfraUtilitiesGitWorktreeCheckpointMixin,
    )
    from flext_infra._utilities._git.worktree_discovery import (
        FlextInfraUtilitiesGitWorktreeDiscoveryMixin,
    )
    from flext_infra._utilities._git.worktree_facts import (
        FlextInfraUtilitiesGitWorktreeFactsMixin,
    )
    from flext_infra._utilities._git.worktree_io import FlextInfraUtilitiesGitWorktreeIO
    from flext_infra._utilities._git.worktree_materialization import (
        FlextInfraUtilitiesGitWorktreeMaterializationMixin,
    )
    from flext_infra._utilities._git.worktree_measure import (
        FlextInfraUtilitiesGitWorktreeMeasureMixin,
    )
    from flext_infra._utilities._git.worktree_patch import (
        FlextInfraUtilitiesGitWorktreePatchMixin,
    )
    from flext_infra._utilities._git.worktree_removal import (
        FlextInfraUtilitiesGitWorktreeRemovalMixin,
    )
    from flext_infra._utilities._git.worktree_roots import (
        FlextInfraUtilitiesGitWorktreeRootsMixin,
    )
    from flext_infra._utilities._git.worktree_status import (
        FlextInfraUtilitiesGitWorktreeStatusMixin,
    )
    from flext_infra._utilities._import_law._policy.namespace import (
        FlextInfraUtilitiesImportLawPolicyNamespace,
    )
    from flext_infra._utilities._import_law._policy.publication import (
        FlextInfraUtilitiesImportLawPolicyPublication,
    )
    from flext_infra._utilities._import_law.ast import FlextInfraUtilitiesImportLawAst
    from flext_infra._utilities._import_law.graph import (
        FlextInfraUtilitiesImportLawGraph,
    )
    from flext_infra._utilities._import_law.normalization import (
        FlextInfraUtilitiesImportLawNormalization,
    )
    from flext_infra._utilities._import_law.placement import (
        FlextInfraUtilitiesImportLawPlacement,
    )
    from flext_infra._utilities._import_law.policy import (
        FlextInfraUtilitiesImportLawPolicy,
    )
    from flext_infra._utilities._import_law.routes import (
        FlextInfraUtilitiesImportLawRoutes,
    )
    from flext_infra._utilities._project.discovery_candidates import (
        FlextInfraUtilitiesProjectDiscoveryCandidates,
    )
    from flext_infra._utilities._project.discovery_shape import (
        FlextInfraUtilitiesProjectDiscoveryShape,
    )
    from flext_infra._utilities._promoted.commands import (
        FlextInfraUtilitiesPromotedCommands,
    )
    from flext_infra._utilities._promoted.execution import (
        FlextInfraUtilitiesPromotedExecution,
    )
    from flext_infra._utilities._promoted.invocation import (
        FlextInfraUtilitiesPromotedInvocation,
    )
    from flext_infra._utilities._promoted.rendering import (
        FlextInfraUtilitiesPromotedRendering,
    )
    from flext_infra._utilities._promoted.workspace import (
        FlextInfraUtilitiesPromotedWorkspace,
    )
    from flext_infra._utilities._pyproject.base import (
        FlextInfraUtilitiesPyprojectConformBase,
    )
    from flext_infra._utilities._pyproject.conform import (
        FlextInfraUtilitiesPyprojectConform,
    )
    from flext_infra._utilities._pyproject.document import (
        FlextInfraUtilitiesPyprojectDocument,
    )
    from flext_infra._utilities._pyproject.overlay import (
        FlextInfraUtilitiesPyprojectOverlay,
    )
    from flext_infra._utilities._pyproject.requirements import (
        FlextInfraUtilitiesPyprojectRequirements,
    )
    from flext_infra._utilities._pyproject.toml_phases import (
        FlextInfraUtilitiesPyprojectTomlPhases,
    )
    from flext_infra._utilities._pyproject.uv_sources import (
        FlextInfraUtilitiesPyprojectUvSources,
    )
    from flext_infra._utilities._rope._analysis.asthelpers import (
        FlextInfraUtilitiesRopeAnalysisAstHelpers,
    )
    from flext_infra._utilities._rope._analysis.base import (
        FlextInfraUtilitiesRopeAnalysisBase,
    )
    from flext_infra._utilities._rope._analysis.exports import (
        FlextInfraUtilitiesRopeAnalysisExports,
    )
    from flext_infra._utilities._rope._analysis.importstate import (
        FlextInfraUtilitiesRopeAnalysisImportState,
    )
    from flext_infra._utilities._rope._analysis.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
        FlextInfraUtilitiesRopeAnalysisWorkspace,
    )
    from flext_infra._utilities._rope._analysis.sourcescan import (
        FlextInfraUtilitiesRopeAnalysisSourceScan,
    )
    from flext_infra._utilities._rope.inventory_sites import (
        FlextInfraUtilitiesRopeInventorySitesMixin,
    )
    from flext_infra._utilities._rope.method_order import (
        FlextInfraUtilitiesRopeMethodOrderMixin,
    )
    from flext_infra._utilities._rope.move_publication import (
        FlextInfraUtilitiesRopeMovePublication,
    )
    from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject
    from flext_infra._utilities._rope.project import FlextInfraRopeProject
    from flext_infra._utilities._rope.pymodule import (
        FlextInfraUtilitiesRopeCorePyModuleMixin,
    )
    from flext_infra._utilities._rope.restructure import FlextInfraRopeRestructure
    from flext_infra._utilities._rope.rope_analysis import (
        FlextInfraUtilitiesRopeAnalysis,
    )
    from flext_infra._utilities._rope.rope_ast import FlextInfraUtilitiesRopeAst
    from flext_infra._utilities._rope.rope_bindings import (
        FlextInfraUtilitiesRopeAstBindings,
    )
    from flext_infra._utilities._rope.rope_class_move import (
        FlextInfraUtilitiesRopeClassMove,
    )
    from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities._rope.rope_core_resources import (
        FlextInfraUtilitiesRopeCoreResourcesMixin,
    )
    from flext_infra._utilities._rope.rope_helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities._rope.rope_imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities._rope.rope_inventory import (
        FlextInfraUtilitiesRopeInventory,
    )
    from flext_infra._utilities._rope.rope_module_patch import (
        FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities._rope.rope_nested_class_move import (
        FlextInfraUtilitiesRopeNestedClassMove,
    )
    from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
    from flext_infra._utilities._rope.rope_runtime_base import (
        FlextInfraUtilitiesRopeRuntimeBase,
    )
    from flext_infra._utilities._rope.rope_runtime_matching import (
        FlextInfraUtilitiesRopeRuntimeMatching,
    )
    from flext_infra._utilities._rope.rope_runtime_module_queries import (
        FlextInfraUtilitiesRopeRuntimeModuleQueries,
    )
    from flext_infra._utilities._rope.rope_runtime_modules import (
        FlextInfraUtilitiesRopeRuntimeModules,
    )
    from flext_infra._utilities._rope.rope_runtime_refactors import (
        FlextInfraUtilitiesRopeRuntimeRefactors,
    )
    from flext_infra._utilities._rope.rope_runtime_types import (
        FlextInfraUtilitiesRopeRuntimeTypes,
    )
    from flext_infra._utilities._rope.rope_source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities._rope.rope_source_bases_runtime import (
        FlextInfraUtilitiesRopeSourceBasesRuntime,
    )
    from flext_infra._utilities._rope.rope_structure import (
        FlextInfraUtilitiesRopeStructure,
    )
    from flext_infra._utilities._rope.source_bases_aliases import (
        FlextInfraUtilitiesRopeSourceBasesAliases,
    )
    from flext_infra._utilities._rope.source_bases_inventory import (
        FlextInfraUtilitiesRopeSourceBasesInventory,
    )
    from flext_infra._utilities._rope.source_bases_inventory_collector import (
        FlextInfraUtilitiesRopeSourceBindingCollector,
    )
    from flext_infra._utilities._semantic_cutover.alias_cst import (
        FlextInfraUtilitiesSemanticCutoverAliasCst,
    )
    from flext_infra._utilities._semantic_cutover.aliases import (
        FlextInfraUtilitiesSemanticCutoverAliases,
    )
    from flext_infra._utilities._semantic_cutover.base import (
        FlextInfraUtilitiesSemanticCutoverBase,
    )
    from flext_infra._utilities._semantic_cutover.bindings import (
        FlextInfraUtilitiesSemanticCutoverBindings,
    )
    from flext_infra._utilities._semantic_cutover.class_scope import (
        FlextInfraUtilitiesSemanticCutoverClassScope,
    )
    from flext_infra._utilities._semantic_cutover.composition import (
        FlextInfraUtilitiesSemanticComposition,
    )
    from flext_infra._utilities._semantic_cutover.constant_consumers import (
        FlextInfraUtilitiesSemanticConstantConsumers,
    )
    from flext_infra._utilities._semantic_cutover.constant_sources import (
        FlextInfraUtilitiesSemanticConstantSources,
    )
    from flext_infra._utilities._semantic_cutover.contracts import (
        FlextInfraUtilitiesSemanticContracts,
    )
    from flext_infra._utilities._semantic_cutover.declaration_payload import (
        FlextInfraUtilitiesDeclarationPayload,
    )
    from flext_infra._utilities._semantic_cutover.declaration_relocation import (
        FlextInfraUtilitiesSemanticDeclarationRelocation,
    )
    from flext_infra._utilities._semantic_cutover.declaration_retirement import (
        FlextInfraUtilitiesSemanticDeclarationRetirement,
    )
    from flext_infra._utilities._semantic_cutover.delegations import (
        FlextInfraUtilitiesSemanticDelegations,
    )
    from flext_infra._utilities._semantic_cutover.dynamic_environment import (
        FlextInfraUtilitiesSemanticCutoverDynamicEnvironment,
    )
    from flext_infra._utilities._semantic_cutover.edits import (
        FlextInfraUtilitiesSemanticCutoverEdits,
    )
    from flext_infra._utilities._semantic_cutover.facade_base_cst import (
        FlextInfraUtilitiesSemanticCutoverFacadeBaseCst,
    )
    from flext_infra._utilities._semantic_cutover.facade_bases import (
        FlextInfraUtilitiesSemanticCutoverFacadeBases,
    )
    from flext_infra._utilities._semantic_cutover.facade_owners import (
        FlextInfraUtilitiesSemanticCutoverFacadeOwners,
    )
    from flext_infra._utilities._semantic_cutover.family_flatten import (
        FlextInfraUtilitiesSemanticFamilyFlatten,
    )
    from flext_infra._utilities._semantic_cutover.family_references import (
        FlextInfraUtilitiesSemanticFamilyReferences,
    )
    from flext_infra._utilities._semantic_cutover.family_type_references import (
        FlextInfraUtilitiesSemanticFamilyTypeReferences,
    )
    from flext_infra._utilities._semantic_cutover.helper_references import (
        FlextInfraUtilitiesSemanticHelperReferences,
    )
    from flext_infra._utilities._semantic_cutover.model_aliases import (
        FlextInfraUtilitiesSemanticModelAliases,
    )
    from flext_infra._utilities._semantic_cutover.model_fields import (
        FlextInfraUtilitiesSemanticCutoverModelFields,
    )
    from flext_infra._utilities._semantic_cutover.model_fields_bindings import (
        FlextInfraUtilitiesSemanticCutoverModelFieldsBindings,
    )
    from flext_infra._utilities._semantic_cutover.module_layout import (
        FlextInfraUtilitiesSemanticCutoverModuleLayout,
    )
    from flext_infra._utilities._semantic_cutover.nesting import (
        FlextInfraUtilitiesSemanticCutoverNesting,
    )
    from flext_infra._utilities._semantic_cutover.nesting_cst import (
        FlextInfraUtilitiesSemanticCutoverNestingCst,
    )
    from flext_infra._utilities._semantic_cutover.nesting_module_aliases import (
        FlextInfraUtilitiesSemanticCutoverNestingModuleAliases,
    )
    from flext_infra._utilities._semantic_cutover.nesting_owner import (
        FlextInfraUtilitiesSemanticCutoverNestingOwner,
    )
    from flext_infra._utilities._semantic_cutover.nesting_references import (
        FlextInfraUtilitiesSemanticCutoverNestingReferences,
    )
    from flext_infra._utilities._semantic_cutover.nesting_types import (
        FlextInfraUtilitiesSemanticNestingTypes,
    )
    from flext_infra._utilities._semantic_cutover.own_mro import (
        FlextInfraUtilitiesSemanticCutoverOwnMro,
    )
    from flext_infra._utilities._semantic_cutover.private_import_cst import (
        FlextInfraUtilitiesSemanticCutoverPrivateImportCst,
    )
    from flext_infra._utilities._semantic_cutover.private_imports import (
        FlextInfraUtilitiesSemanticCutoverPrivateImports,
    )
    from flext_infra._utilities._semantic_cutover.self_facade import (
        FlextInfraUtilitiesSemanticCutoverSelfFacade,
    )
    from flext_infra._utilities._semantic_cutover.test_helpers import (
        FlextInfraUtilitiesSemanticTestHelpers,
    )
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
    from flext_infra._utilities.protocol_models import FlextInfraUtilitiesProtocolModels
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
    "FlextInfraRopeNativeProject",
    "FlextInfraRopeProject",
    "FlextInfraRopeRestructure",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenFacadeSyntax",
    "FlextInfraUtilitiesCodegenFacades",
    "FlextInfraUtilitiesCodegenFilePlan",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesCodemod",
    "FlextInfraUtilitiesCodemodBindingChain",
    "FlextInfraUtilitiesCodemodImportLawRules",
    "FlextInfraUtilitiesCodemodNativeCascade",
    "FlextInfraUtilitiesCodemodNativePackageUtilities",
    "FlextInfraUtilitiesCodemodNativeUtilities",
    "FlextInfraUtilitiesCodemodProject",
    "FlextInfraUtilitiesCodemodProjectFacts",
    "FlextInfraUtilitiesCodemodRules",
    "FlextInfraUtilitiesCodemodRulesDistributions",
    "FlextInfraUtilitiesCodemodScopes",
    "FlextInfraUtilitiesCodemodTypeSetRules",
    "FlextInfraUtilitiesCompatibilityAliasValidation",
    "FlextInfraUtilitiesDeclarationPayload",
    "FlextInfraUtilitiesDeferredSelfReferenceRewrite",
    "FlextInfraUtilitiesDependencies",
    "FlextInfraUtilitiesDependency",
    "FlextInfraUtilitiesDependencyDeptry",
    "FlextInfraUtilitiesDependencyRequirements",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsAuditDetectors",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsCollection",
    "FlextInfraUtilitiesDocsCollectionSources",
    "FlextInfraUtilitiesDocsCommandContract",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsGeneratePlan",
    "FlextInfraUtilitiesDocsGenerateProject",
    "FlextInfraUtilitiesDocsGenerateRoot",
    "FlextInfraUtilitiesDocsGenerateSources",
    "FlextInfraUtilitiesDocsGithubLinks",
    "FlextInfraUtilitiesDocsGuides",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsScopeBuild",
    "FlextInfraUtilitiesDocsScopePaths",
    "FlextInfraUtilitiesDocsScopePolicy",
    "FlextInfraUtilitiesDocsScopeProjectsMixin",
    "FlextInfraUtilitiesDocsScopeSelection",
    "FlextInfraUtilitiesDocsScopeState",
    "FlextInfraUtilitiesDocsValidate",
    "FlextInfraUtilitiesEnforcementCatalog",
    "FlextInfraUtilitiesFacadeComponents",
    "FlextInfraUtilitiesFacadeMembers",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGitAttestationEvidenceMixin",
    "FlextInfraUtilitiesGitAttestationMixin",
    "FlextInfraUtilitiesGitLaneHygieneMixin",
    "FlextInfraUtilitiesGitMutationScopeMixin",
    "FlextInfraUtilitiesGitRemote",
    "FlextInfraUtilitiesGitRepo",
    "FlextInfraUtilitiesGitRequirementSource",
    "FlextInfraUtilitiesGitScopeMixin",
    "FlextInfraUtilitiesGitSemanticIdentityMixin",
    "FlextInfraUtilitiesGitSemanticIndexMixin",
    "FlextInfraUtilitiesGitSemanticLaneMixin",
    "FlextInfraUtilitiesGitSemanticPathsMixin",
    "FlextInfraUtilitiesGitSemanticPublishMixin",
    "FlextInfraUtilitiesGitSemanticRefsMixin",
    "FlextInfraUtilitiesGitSemanticSubmoduleMixin",
    "FlextInfraUtilitiesGitSemanticWorktreeMixin",
    "FlextInfraUtilitiesGitStateCaptureMixin",
    "FlextInfraUtilitiesGitStateCheckpointMixin",
    "FlextInfraUtilitiesGitStateFilesMixin",
    "FlextInfraUtilitiesGitStatePublicationMixin",
    "FlextInfraUtilitiesGitStateSnapshotMixin",
    "FlextInfraUtilitiesGitStateTransitionMixin",
    "FlextInfraUtilitiesGitStateTreesMixin",
    "FlextInfraUtilitiesGitWorktreeCheckpointMixin",
    "FlextInfraUtilitiesGitWorktreeDiscoveryMixin",
    "FlextInfraUtilitiesGitWorktreeFactsMixin",
    "FlextInfraUtilitiesGitWorktreeIO",
    "FlextInfraUtilitiesGitWorktreeMaterializationMixin",
    "FlextInfraUtilitiesGitWorktreeMeasureMixin",
    "FlextInfraUtilitiesGitWorktreeMixin",
    "FlextInfraUtilitiesGitWorktreePatchMixin",
    "FlextInfraUtilitiesGitWorktreeRemovalMixin",
    "FlextInfraUtilitiesGitWorktreeRootsMixin",
    "FlextInfraUtilitiesGitWorktreeStatusMixin",
    "FlextInfraUtilitiesGitignore",
    "FlextInfraUtilitiesImportLaw",
    "FlextInfraUtilitiesImportLawAst",
    "FlextInfraUtilitiesImportLawGraph",
    "FlextInfraUtilitiesImportLawNormalization",
    "FlextInfraUtilitiesImportLawPlacement",
    "FlextInfraUtilitiesImportLawPolicy",
    "FlextInfraUtilitiesImportLawPolicyNamespace",
    "FlextInfraUtilitiesImportLawPolicyPublication",
    "FlextInfraUtilitiesImportLawRoutes",
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
    "FlextInfraUtilitiesProjectDiscoveryCandidates",
    "FlextInfraUtilitiesProjectDiscoveryShape",
    "FlextInfraUtilitiesProjectManagedArtifacts",
    "FlextInfraUtilitiesPromoted",
    "FlextInfraUtilitiesPromotedCommands",
    "FlextInfraUtilitiesPromotedExecution",
    "FlextInfraUtilitiesPromotedInvocation",
    "FlextInfraUtilitiesPromotedRendering",
    "FlextInfraUtilitiesPromotedWorkspace",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesProtectedEditApply",
    "FlextInfraUtilitiesProtectedEditLinting",
    "FlextInfraUtilitiesProtectedEditPreview",
    "FlextInfraUtilitiesProtectedEditWrites",
    "FlextInfraUtilitiesProtocolModels",
    "FlextInfraUtilitiesPyprojectConform",
    "FlextInfraUtilitiesPyprojectConformBase",
    "FlextInfraUtilitiesPyprojectDocument",
    "FlextInfraUtilitiesPyprojectOverlay",
    "FlextInfraUtilitiesPyprojectRequirements",
    "FlextInfraUtilitiesPyprojectTomlPhases",
    "FlextInfraUtilitiesPyprojectUvSources",
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
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAnalysisAstHelpers",
    "FlextInfraUtilitiesRopeAnalysisBase",
    "FlextInfraUtilitiesRopeAnalysisExports",
    "FlextInfraUtilitiesRopeAnalysisImportState",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeAnalysisSourceScan",
    "FlextInfraUtilitiesRopeAnalysisWorkspace",
    "FlextInfraUtilitiesRopeAst",
    "FlextInfraUtilitiesRopeAstBindings",
    "FlextInfraUtilitiesRopeClassMove",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeCorePyModuleMixin",
    "FlextInfraUtilitiesRopeCoreResourcesMixin",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeInventory",
    "FlextInfraUtilitiesRopeInventorySitesMixin",
    "FlextInfraUtilitiesRopeMethodOrderMixin",
    "FlextInfraUtilitiesRopeModulePatch",
    "FlextInfraUtilitiesRopeMovePublication",
    "FlextInfraUtilitiesRopeNestedClassMove",
    "FlextInfraUtilitiesRopeRuntime",
    "FlextInfraUtilitiesRopeRuntimeBase",
    "FlextInfraUtilitiesRopeRuntimeMatching",
    "FlextInfraUtilitiesRopeRuntimeModuleQueries",
    "FlextInfraUtilitiesRopeRuntimeModules",
    "FlextInfraUtilitiesRopeRuntimeRefactors",
    "FlextInfraUtilitiesRopeRuntimeTypes",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesRopeSourceBasesAliases",
    "FlextInfraUtilitiesRopeSourceBasesInventory",
    "FlextInfraUtilitiesRopeSourceBasesRuntime",
    "FlextInfraUtilitiesRopeSourceBindingCollector",
    "FlextInfraUtilitiesRopeStructure",
    "FlextInfraUtilitiesSemanticComposition",
    "FlextInfraUtilitiesSemanticConstantConsumers",
    "FlextInfraUtilitiesSemanticConstantSources",
    "FlextInfraUtilitiesSemanticContracts",
    "FlextInfraUtilitiesSemanticCutover",
    "FlextInfraUtilitiesSemanticCutoverAliasCst",
    "FlextInfraUtilitiesSemanticCutoverAliases",
    "FlextInfraUtilitiesSemanticCutoverBase",
    "FlextInfraUtilitiesSemanticCutoverBindings",
    "FlextInfraUtilitiesSemanticCutoverClassScope",
    "FlextInfraUtilitiesSemanticCutoverDynamicEnvironment",
    "FlextInfraUtilitiesSemanticCutoverEdits",
    "FlextInfraUtilitiesSemanticCutoverFacadeBaseCst",
    "FlextInfraUtilitiesSemanticCutoverFacadeBases",
    "FlextInfraUtilitiesSemanticCutoverFacadeOwners",
    "FlextInfraUtilitiesSemanticCutoverModelFields",
    "FlextInfraUtilitiesSemanticCutoverModelFieldsBindings",
    "FlextInfraUtilitiesSemanticCutoverModuleLayout",
    "FlextInfraUtilitiesSemanticCutoverNesting",
    "FlextInfraUtilitiesSemanticCutoverNestingCst",
    "FlextInfraUtilitiesSemanticCutoverNestingModuleAliases",
    "FlextInfraUtilitiesSemanticCutoverNestingOwner",
    "FlextInfraUtilitiesSemanticCutoverNestingReferences",
    "FlextInfraUtilitiesSemanticCutoverOwnMro",
    "FlextInfraUtilitiesSemanticCutoverPrivateImportCst",
    "FlextInfraUtilitiesSemanticCutoverPrivateImports",
    "FlextInfraUtilitiesSemanticCutoverSelfFacade",
    "FlextInfraUtilitiesSemanticDeclarationRelocation",
    "FlextInfraUtilitiesSemanticDeclarationRetirement",
    "FlextInfraUtilitiesSemanticDelegations",
    "FlextInfraUtilitiesSemanticFamilyFlatten",
    "FlextInfraUtilitiesSemanticFamilyReferences",
    "FlextInfraUtilitiesSemanticFamilyTypeReferences",
    "FlextInfraUtilitiesSemanticHelperReferences",
    "FlextInfraUtilitiesSemanticModelAliases",
    "FlextInfraUtilitiesSemanticNestingTypes",
    "FlextInfraUtilitiesSemanticTestHelpers",
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
        "FlextInfraRopeNativeProject": "._rope.native_project",
        "FlextInfraRopeProject": "._rope.project",
        "FlextInfraRopeRestructure": "._rope.restructure",
        "FlextInfraUtilitiesBase": ".base",
        "FlextInfraUtilitiesCodegen": ".codegen",
        "FlextInfraUtilitiesCodegenFacadeSyntax": ".codegen_facade_syntax",
        "FlextInfraUtilitiesCodegenFacades": ".codegen_facades",
        "FlextInfraUtilitiesCodegenFilePlan": ".codegen_file_plan",
        "FlextInfraUtilitiesCodegenNamespace": ".namespace",
        "FlextInfraUtilitiesCodemod": ".codemod",
        "FlextInfraUtilitiesCodemodBindingChain": "._codemod.codemod_binding_chain",
        "FlextInfraUtilitiesCodemodImportLawRules": "._codemod.codemod_import_law_rules",
        "FlextInfraUtilitiesCodemodNativeCascade": "._codemod.codemod_native_cascade",
        "FlextInfraUtilitiesCodemodNativePackageUtilities": "._codemod.codemod_native_package_utilities",
        "FlextInfraUtilitiesCodemodNativeUtilities": "._codemod.codemod_native_utilities",
        "FlextInfraUtilitiesCodemodProject": "._codemod.codemod_project",
        "FlextInfraUtilitiesCodemodProjectFacts": "._codemod.codemod_project_facts",
        "FlextInfraUtilitiesCodemodRules": "._codemod.codemod_rules",
        "FlextInfraUtilitiesCodemodRulesDistributions": "._codemod.rules_distributions",
        "FlextInfraUtilitiesCodemodScopes": "._codemod.codemod_scopes",
        "FlextInfraUtilitiesCodemodTypeSetRules": "._codemod.codemod_type_set_rules",
        "FlextInfraUtilitiesCompatibilityAliasValidation": ".compatibility_alias_validation",
        "FlextInfraUtilitiesDeclarationPayload": "._semantic_cutover.declaration_payload",
        "FlextInfraUtilitiesDeferredSelfReferenceRewrite": ".deferred_self_reference_rewrite",
        "FlextInfraUtilitiesDependencies": ".dependencies",
        "FlextInfraUtilitiesDependency": ".dependency",
        "FlextInfraUtilitiesDependencyDeptry": "._dependency.deptry",
        "FlextInfraUtilitiesDependencyRequirements": ".dependency_requirements",
        "FlextInfraUtilitiesDiscovery": ".discovery",
        "FlextInfraUtilitiesDocs": ".docs",
        "FlextInfraUtilitiesDocsApi": "._docs.docs_api",
        "FlextInfraUtilitiesDocsAudit": "._docs.docs_audit",
        "FlextInfraUtilitiesDocsAuditDetectors": "._docs.audit_detectors",
        "FlextInfraUtilitiesDocsBuild": "._docs.docs_build",
        "FlextInfraUtilitiesDocsCollection": "._docs.docs_collection",
        "FlextInfraUtilitiesDocsCollectionSources": "._docs.docs_collection_sources",
        "FlextInfraUtilitiesDocsCommandContract": "._docs.command_contract",
        "FlextInfraUtilitiesDocsContract": "._docs.docs_contract",
        "FlextInfraUtilitiesDocsFix": "._docs.docs_fix",
        "FlextInfraUtilitiesDocsGenerate": "._docs.docs_generate",
        "FlextInfraUtilitiesDocsGeneratePlan": "._docs.generate_plan",
        "FlextInfraUtilitiesDocsGenerateProject": "._docs.generate_project",
        "FlextInfraUtilitiesDocsGenerateRoot": "._docs.generate_root",
        "FlextInfraUtilitiesDocsGenerateSources": "._docs.generate_sources",
        "FlextInfraUtilitiesDocsGithubLinks": "._docs.github_links",
        "FlextInfraUtilitiesDocsGuides": "._docs.guides",
        "FlextInfraUtilitiesDocsRender": "._docs.docs_render",
        "FlextInfraUtilitiesDocsScope": "._docs.docs_scope",
        "FlextInfraUtilitiesDocsScopeBuild": "._docs.scope_build",
        "FlextInfraUtilitiesDocsScopePaths": "._docs.scope_paths",
        "FlextInfraUtilitiesDocsScopePolicy": "._docs.scope_policy",
        "FlextInfraUtilitiesDocsScopeProjectsMixin": "._docs.docs_scope_projects",
        "FlextInfraUtilitiesDocsScopeSelection": "._docs.scope_selection",
        "FlextInfraUtilitiesDocsScopeState": "._docs.scope_state",
        "FlextInfraUtilitiesDocsValidate": "._docs.docs_validate",
        "FlextInfraUtilitiesEnforcementCatalog": ".enforcement_catalog",
        "FlextInfraUtilitiesFacadeComponents": ".facade_components",
        "FlextInfraUtilitiesFacadeMembers": ".facade_members",
        "FlextInfraUtilitiesGit": ".git",
        "FlextInfraUtilitiesGitAttestationEvidenceMixin": "._git.attestation_evidence",
        "FlextInfraUtilitiesGitAttestationMixin": "._git.attestation",
        "FlextInfraUtilitiesGitLaneHygieneMixin": "._git.lane_hygiene",
        "FlextInfraUtilitiesGitMutationScopeMixin": "._git.mutation_scope",
        "FlextInfraUtilitiesGitRemote": "._git.remote",
        "FlextInfraUtilitiesGitRepo": "._git.repo",
        "FlextInfraUtilitiesGitRequirementSource": "._git.requirement_source",
        "FlextInfraUtilitiesGitScopeMixin": "._git.scope",
        "FlextInfraUtilitiesGitSemanticIdentityMixin": "._git.semantic_identity",
        "FlextInfraUtilitiesGitSemanticIndexMixin": "._git.semantic_index",
        "FlextInfraUtilitiesGitSemanticLaneMixin": "._git.semantic_lane",
        "FlextInfraUtilitiesGitSemanticPathsMixin": "._git.semantic_paths",
        "FlextInfraUtilitiesGitSemanticPublishMixin": "._git.semantic_publish",
        "FlextInfraUtilitiesGitSemanticRefsMixin": "._git.semantic_refs",
        "FlextInfraUtilitiesGitSemanticSubmoduleMixin": "._git.semantic_submodule",
        "FlextInfraUtilitiesGitSemanticWorktreeMixin": "._git.semantic_worktree",
        "FlextInfraUtilitiesGitStateCaptureMixin": "._git.state_capture",
        "FlextInfraUtilitiesGitStateCheckpointMixin": "._git.state_checkpoint",
        "FlextInfraUtilitiesGitStateFilesMixin": "._git.state_files",
        "FlextInfraUtilitiesGitStatePublicationMixin": "._git.state_publication",
        "FlextInfraUtilitiesGitStateSnapshotMixin": "._git.state_snapshot",
        "FlextInfraUtilitiesGitStateTransitionMixin": "._git.state_transition",
        "FlextInfraUtilitiesGitStateTreesMixin": "._git.state_trees",
        "FlextInfraUtilitiesGitWorktreeCheckpointMixin": "._git.worktree_checkpoint",
        "FlextInfraUtilitiesGitWorktreeDiscoveryMixin": "._git.worktree_discovery",
        "FlextInfraUtilitiesGitWorktreeFactsMixin": "._git.worktree_facts",
        "FlextInfraUtilitiesGitWorktreeIO": "._git.worktree_io",
        "FlextInfraUtilitiesGitWorktreeMaterializationMixin": "._git.worktree_materialization",
        "FlextInfraUtilitiesGitWorktreeMeasureMixin": "._git.worktree_measure",
        "FlextInfraUtilitiesGitWorktreeMixin": "._git.worktree",
        "FlextInfraUtilitiesGitWorktreePatchMixin": "._git.worktree_patch",
        "FlextInfraUtilitiesGitWorktreeRemovalMixin": "._git.worktree_removal",
        "FlextInfraUtilitiesGitWorktreeRootsMixin": "._git.worktree_roots",
        "FlextInfraUtilitiesGitWorktreeStatusMixin": "._git.worktree_status",
        "FlextInfraUtilitiesGitignore": "._git.gitignore",
        "FlextInfraUtilitiesImportLaw": ".import_law",
        "FlextInfraUtilitiesImportLawAst": "._import_law.ast",
        "FlextInfraUtilitiesImportLawGraph": "._import_law.graph",
        "FlextInfraUtilitiesImportLawNormalization": "._import_law.normalization",
        "FlextInfraUtilitiesImportLawPlacement": "._import_law.placement",
        "FlextInfraUtilitiesImportLawPolicy": "._import_law.policy",
        "FlextInfraUtilitiesImportLawPolicyNamespace": "._import_law._policy.namespace",
        "FlextInfraUtilitiesImportLawPolicyPublication": "._import_law._policy.publication",
        "FlextInfraUtilitiesImportLawRoutes": "._import_law.routes",
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
        "FlextInfraUtilitiesProjectDiscoveryCandidates": "._project.discovery_candidates",
        "FlextInfraUtilitiesProjectDiscoveryShape": "._project.discovery_shape",
        "FlextInfraUtilitiesProjectManagedArtifacts": ".project_managed_artifacts",
        "FlextInfraUtilitiesPromoted": ".promoted",
        "FlextInfraUtilitiesPromotedCommands": "._promoted.commands",
        "FlextInfraUtilitiesPromotedExecution": "._promoted.execution",
        "FlextInfraUtilitiesPromotedInvocation": "._promoted.invocation",
        "FlextInfraUtilitiesPromotedRendering": "._promoted.rendering",
        "FlextInfraUtilitiesPromotedWorkspace": "._promoted.workspace",
        "FlextInfraUtilitiesProtectedEdit": ".protected_edit",
        "FlextInfraUtilitiesProtectedEditApply": ".protected_edit_apply",
        "FlextInfraUtilitiesProtectedEditLinting": ".protected_edit_linting",
        "FlextInfraUtilitiesProtectedEditPreview": ".protected_edit_preview",
        "FlextInfraUtilitiesProtectedEditWrites": ".protected_edit_writes",
        "FlextInfraUtilitiesProtocolModels": ".protocol_models",
        "FlextInfraUtilitiesPyprojectConform": "._pyproject.conform",
        "FlextInfraUtilitiesPyprojectConformBase": "._pyproject.base",
        "FlextInfraUtilitiesPyprojectDocument": "._pyproject.document",
        "FlextInfraUtilitiesPyprojectOverlay": "._pyproject.overlay",
        "FlextInfraUtilitiesPyprojectRequirements": "._pyproject.requirements",
        "FlextInfraUtilitiesPyprojectTomlPhases": "._pyproject.toml_phases",
        "FlextInfraUtilitiesPyprojectUvSources": "._pyproject.uv_sources",
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
        "FlextInfraUtilitiesRopeAnalysis": "._rope.rope_analysis",
        "FlextInfraUtilitiesRopeAnalysisAstHelpers": "._rope._analysis.asthelpers",
        "FlextInfraUtilitiesRopeAnalysisBase": "._rope._analysis.base",
        "FlextInfraUtilitiesRopeAnalysisExports": "._rope._analysis.exports",
        "FlextInfraUtilitiesRopeAnalysisImportState": "._rope._analysis.importstate",
        "FlextInfraUtilitiesRopeAnalysisIntrospection": "._rope._analysis.rope_analysis_introspection",
        "FlextInfraUtilitiesRopeAnalysisSourceScan": "._rope._analysis.sourcescan",
        "FlextInfraUtilitiesRopeAnalysisWorkspace": "._rope._analysis.rope_analysis_workspace",
        "FlextInfraUtilitiesRopeAst": "._rope.rope_ast",
        "FlextInfraUtilitiesRopeAstBindings": "._rope.rope_bindings",
        "FlextInfraUtilitiesRopeClassMove": "._rope.rope_class_move",
        "FlextInfraUtilitiesRopeCore": "._rope.rope_core",
        "FlextInfraUtilitiesRopeCorePyModuleMixin": "._rope.pymodule",
        "FlextInfraUtilitiesRopeCoreResourcesMixin": "._rope.rope_core_resources",
        "FlextInfraUtilitiesRopeHelpers": "._rope.rope_helpers",
        "FlextInfraUtilitiesRopeImports": "._rope.rope_imports",
        "FlextInfraUtilitiesRopeInventory": "._rope.rope_inventory",
        "FlextInfraUtilitiesRopeInventorySitesMixin": "._rope.inventory_sites",
        "FlextInfraUtilitiesRopeMethodOrderMixin": "._rope.method_order",
        "FlextInfraUtilitiesRopeModulePatch": "._rope.rope_module_patch",
        "FlextInfraUtilitiesRopeMovePublication": "._rope.move_publication",
        "FlextInfraUtilitiesRopeNestedClassMove": "._rope.rope_nested_class_move",
        "FlextInfraUtilitiesRopeRuntime": "._rope.rope_runtime",
        "FlextInfraUtilitiesRopeRuntimeBase": "._rope.rope_runtime_base",
        "FlextInfraUtilitiesRopeRuntimeMatching": "._rope.rope_runtime_matching",
        "FlextInfraUtilitiesRopeRuntimeModuleQueries": "._rope.rope_runtime_module_queries",
        "FlextInfraUtilitiesRopeRuntimeModules": "._rope.rope_runtime_modules",
        "FlextInfraUtilitiesRopeRuntimeRefactors": "._rope.rope_runtime_refactors",
        "FlextInfraUtilitiesRopeRuntimeTypes": "._rope.rope_runtime_types",
        "FlextInfraUtilitiesRopeSource": "._rope.rope_source",
        "FlextInfraUtilitiesRopeSourceBasesAliases": "._rope.source_bases_aliases",
        "FlextInfraUtilitiesRopeSourceBasesInventory": "._rope.source_bases_inventory",
        "FlextInfraUtilitiesRopeSourceBasesRuntime": "._rope.rope_source_bases_runtime",
        "FlextInfraUtilitiesRopeSourceBindingCollector": "._rope.source_bases_inventory_collector",
        "FlextInfraUtilitiesRopeStructure": "._rope.rope_structure",
        "FlextInfraUtilitiesSemanticComposition": "._semantic_cutover.composition",
        "FlextInfraUtilitiesSemanticConstantConsumers": "._semantic_cutover.constant_consumers",
        "FlextInfraUtilitiesSemanticConstantSources": "._semantic_cutover.constant_sources",
        "FlextInfraUtilitiesSemanticContracts": "._semantic_cutover.contracts",
        "FlextInfraUtilitiesSemanticCutover": ".semantic_cutover",
        "FlextInfraUtilitiesSemanticCutoverAliasCst": "._semantic_cutover.alias_cst",
        "FlextInfraUtilitiesSemanticCutoverAliases": "._semantic_cutover.aliases",
        "FlextInfraUtilitiesSemanticCutoverBase": "._semantic_cutover.base",
        "FlextInfraUtilitiesSemanticCutoverBindings": "._semantic_cutover.bindings",
        "FlextInfraUtilitiesSemanticCutoverClassScope": "._semantic_cutover.class_scope",
        "FlextInfraUtilitiesSemanticCutoverDynamicEnvironment": "._semantic_cutover.dynamic_environment",
        "FlextInfraUtilitiesSemanticCutoverEdits": "._semantic_cutover.edits",
        "FlextInfraUtilitiesSemanticCutoverFacadeBaseCst": "._semantic_cutover.facade_base_cst",
        "FlextInfraUtilitiesSemanticCutoverFacadeBases": "._semantic_cutover.facade_bases",
        "FlextInfraUtilitiesSemanticCutoverFacadeOwners": "._semantic_cutover.facade_owners",
        "FlextInfraUtilitiesSemanticCutoverModelFields": "._semantic_cutover.model_fields",
        "FlextInfraUtilitiesSemanticCutoverModelFieldsBindings": "._semantic_cutover.model_fields_bindings",
        "FlextInfraUtilitiesSemanticCutoverModuleLayout": "._semantic_cutover.module_layout",
        "FlextInfraUtilitiesSemanticCutoverNesting": "._semantic_cutover.nesting",
        "FlextInfraUtilitiesSemanticCutoverNestingCst": "._semantic_cutover.nesting_cst",
        "FlextInfraUtilitiesSemanticCutoverNestingModuleAliases": "._semantic_cutover.nesting_module_aliases",
        "FlextInfraUtilitiesSemanticCutoverNestingOwner": "._semantic_cutover.nesting_owner",
        "FlextInfraUtilitiesSemanticCutoverNestingReferences": "._semantic_cutover.nesting_references",
        "FlextInfraUtilitiesSemanticCutoverOwnMro": "._semantic_cutover.own_mro",
        "FlextInfraUtilitiesSemanticCutoverPrivateImportCst": "._semantic_cutover.private_import_cst",
        "FlextInfraUtilitiesSemanticCutoverPrivateImports": "._semantic_cutover.private_imports",
        "FlextInfraUtilitiesSemanticCutoverSelfFacade": "._semantic_cutover.self_facade",
        "FlextInfraUtilitiesSemanticDeclarationRelocation": "._semantic_cutover.declaration_relocation",
        "FlextInfraUtilitiesSemanticDeclarationRetirement": "._semantic_cutover.declaration_retirement",
        "FlextInfraUtilitiesSemanticDelegations": "._semantic_cutover.delegations",
        "FlextInfraUtilitiesSemanticFamilyFlatten": "._semantic_cutover.family_flatten",
        "FlextInfraUtilitiesSemanticFamilyReferences": "._semantic_cutover.family_references",
        "FlextInfraUtilitiesSemanticFamilyTypeReferences": "._semantic_cutover.family_type_references",
        "FlextInfraUtilitiesSemanticHelperReferences": "._semantic_cutover.helper_references",
        "FlextInfraUtilitiesSemanticModelAliases": "._semantic_cutover.model_aliases",
        "FlextInfraUtilitiesSemanticNestingTypes": "._semantic_cutover.nesting_types",
        "FlextInfraUtilitiesSemanticTestHelpers": "._semantic_cutover.test_helpers",
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
