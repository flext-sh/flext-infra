# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports
from flext_infra.__version__ import (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)
from flext_infra._constants._exports import FLEXT_INFRA_LAZY_IMPORTS

if TYPE_CHECKING:
    from flext_core import d as d, e as e, h as h, r as r, x as x
    from flext_core import d, e, h, r, x
    from flext_infra._constants.base import (
        FlextInfraConstantsBase as FlextInfraConstantsBase,
    )
    from flext_infra._constants.basemk import (
        FlextInfraConstantsBasemk as FlextInfraConstantsBasemk,
    )
    from flext_infra._constants.census import (
        FlextInfraConstantsCensus as FlextInfraConstantsCensus,
    )
    from flext_infra._constants.check import (
        FlextInfraConstantsCheck as FlextInfraConstantsCheck,
    )
    from flext_infra._constants.codegen import (
        FlextInfraConstantsCodegen as FlextInfraConstantsCodegen,
    )
    from flext_infra._constants.deps import (
        FlextInfraConstantsDeps as FlextInfraConstantsDeps,
    )
    from flext_infra._constants.docs import (
        FlextInfraConstantsDocs as FlextInfraConstantsDocs,
    )
    from flext_infra._constants.github import (
        FlextInfraConstantsGithub as FlextInfraConstantsGithub,
    )
    from flext_infra._constants.make import (
        FlextInfraConstantsMake as FlextInfraConstantsMake,
    )
    from flext_infra._constants.namespace import (
        FlextInfraConstantsNamespace as FlextInfraConstantsNamespace,
    )
    from flext_infra._constants.refactor import (
        FlextInfraConstantsRefactor as FlextInfraConstantsRefactor,
    )
    from flext_infra._constants.release import (
        FlextInfraConstantsRelease as FlextInfraConstantsRelease,
    )
    from flext_infra._constants.rope import (
        FlextInfraConstantsRope as FlextInfraConstantsRope,
    )
    from flext_infra._constants.source_code import (
        FlextInfraConstantsSourceCode as FlextInfraConstantsSourceCode,
    )
    from flext_infra._constants.validate import (
        FlextInfraConstantsSharedInfra as FlextInfraConstantsSharedInfra,
    )
    from flext_infra._constants.workspace import (
        FlextInfraConstantsWorkspace as FlextInfraConstantsWorkspace,
    )
    from flext_infra._models.base import FlextInfraModelsBase as FlextInfraModelsBase
    from flext_infra._models.basemk import (
        FlextInfraModelsBasemk as FlextInfraModelsBasemk,
    )
    from flext_infra._models.census import (
        FlextInfraModelsCensus as FlextInfraModelsCensus,
    )
    from flext_infra._models.check import FlextInfraModelsCheck as FlextInfraModelsCheck
    from flext_infra._models.codegen import (
        FlextInfraModelsCodegen as FlextInfraModelsCodegen,
    )
    from flext_infra._models.deps import FlextInfraModelsDeps as FlextInfraModelsDeps
    from flext_infra._models.deps_tool_config import (
        FlextInfraModelsDepsToolSettings as FlextInfraModelsDepsToolSettings,
    )
    from flext_infra._models.deps_tool_config_linters import (
        FlextInfraModelsDepsToolConfigLinters as FlextInfraModelsDepsToolConfigLinters,
    )
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraModelsDepsToolConfigTypeCheckers as FlextInfraModelsDepsToolConfigTypeCheckers,
    )
    from flext_infra._models.docs import FlextInfraModelsDocs as FlextInfraModelsDocs
    from flext_infra._models.engine import (
        FlextInfraModelsEngine as FlextInfraModelsEngine,
    )
    from flext_infra._models.engine_ops import (
        FlextInfraModelsEngineOperation as FlextInfraModelsEngineOperation,
    )
    from flext_infra._models.gates import FlextInfraModelsGates as FlextInfraModelsGates
    from flext_infra._models.github import (
        FlextInfraModelsGithub as FlextInfraModelsGithub,
    )
    from flext_infra._models.mixins import (
        FlextInfraModelsMixins as FlextInfraModelsMixins,
    )
    from flext_infra._models.mro_scan import (
        FlextInfraModelsMroScan as FlextInfraModelsMroScan,
    )
    from flext_infra._models.refactor import (
        FlextInfraModelsRefactor as FlextInfraModelsRefactor,
    )
    from flext_infra._models.refactor_ast_grep import (
        FlextInfraModelsRefactorGrep as FlextInfraModelsRefactorGrep,
    )
    from flext_infra._models.refactor_census import (
        FlextInfraModelsRefactorCensus as FlextInfraModelsRefactorCensus,
    )
    from flext_infra._models.refactor_namespace_enforcer import (
        FlextInfraModelsNamespaceEnforcer as FlextInfraModelsNamespaceEnforcer,
    )
    from flext_infra._models.refactor_violations import (
        FlextInfraModelsRefactorViolations as FlextInfraModelsRefactorViolations,
    )
    from flext_infra._models.release import (
        FlextInfraModelsRelease as FlextInfraModelsRelease,
    )
    from flext_infra._models.rope import FlextInfraModelsRope as FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan as FlextInfraModelsScan
    from flext_infra._models.validate import (
        FlextInfraModelsCore as FlextInfraModelsCore,
    )
    from flext_infra._models.workspace import (
        FlextInfraModelsWorkspace as FlextInfraModelsWorkspace,
    )
    from flext_infra._protocols.base import (
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
    )
    from flext_infra._protocols.check import (
        FlextInfraProtocolsCheck as FlextInfraProtocolsCheck,
    )
    from flext_infra._protocols.rope import (
        FlextInfraProtocolsRope as FlextInfraProtocolsRope,
    )
    from flext_infra._typings.adapters import (
        FlextInfraTypesAdapters as FlextInfraTypesAdapters,
    )
    from flext_infra._typings.base import FlextInfraTypesBase as FlextInfraTypesBase
    from flext_infra._typings.rope import FlextInfraTypesRope as FlextInfraTypesRope
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
    from flext_infra._utilities.deps_path_sync import (
        FlextInfraUtilitiesDependencyPathSync as FlextInfraUtilitiesDependencyPathSync,
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
    from flext_infra._utilities.engine import (
        FlextInfraUtilitiesRefactorEngine as FlextInfraUtilitiesRefactorEngine,
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
    from flext_infra._utilities.refactor import (
        FlextInfraUtilitiesRefactor as FlextInfraUtilitiesRefactor,
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
    from flext_infra._utilities.rope_source import (
        FlextInfraUtilitiesRopeSource as FlextInfraUtilitiesRopeSource,
    )
    from flext_infra._utilities.safety import (
        FlextInfraUtilitiesSafety as FlextInfraUtilitiesSafety,
    )
    from flext_infra._utilities.snapshot import (
        FlextInfraUtilitiesSnapshot as FlextInfraUtilitiesSnapshot,
    )
    from flext_infra._utilities.versioning import (
        FlextInfraUtilitiesVersioning as FlextInfraUtilitiesVersioning,
    )
>>>>>>> Stashed changes
    from flext_infra.api import FlextInfra as FlextInfra, infra as infra
    from flext_infra.base import FlextInfraServiceBase as FlextInfraServiceBase, s as s
    from flext_infra.base_selection import (
        FlextInfraProjectSelectionServiceBase as FlextInfraProjectSelectionServiceBase,
<<<<<<< Updated upstream
    )
    from flext_infra.cli import FlextInfraCli as FlextInfraCli, main as main
    from flext_infra.constants import FlextInfraConstants as FlextInfraConstants, c as c
    from flext_infra.fixers.base import FlextInfraFixerAdapter as FlextInfraFixerAdapter
    from flext_infra.fixers.gate_fixer import (
        FlextInfraGateFixerAdapter as FlextInfraGateFixerAdapter,
=======
        FlextInfraServiceBase as FlextInfraServiceBase,
        s,
    )
    from flext_infra.basemk.engine import (
        FlextInfraBaseMkTemplateEngine as FlextInfraBaseMkTemplateEngine,
    )
    from flext_infra.basemk.generator import (
        FlextInfraBaseMkGenerator as FlextInfraBaseMkGenerator,
    )
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker as FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check_gates import (
        FlextInfraGateRegistry as FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin as FlextInfraWorkspaceCheckGatesMixin,
    )
    from flext_infra.cli import FlextInfraCli as FlextInfraCli, main as main
    from flext_infra.codegen.census import (
        FlextInfraCodegenCensus as FlextInfraCodegenCensus,
    )
    from flext_infra.codegen.codegen_generation import (
        FlextInfraCodegenGeneration as FlextInfraCodegenGeneration,
    )
    from flext_infra.codegen.consolidator import (
        FlextInfraCodegenConsolidator as FlextInfraCodegenConsolidator,
    )
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenQualityGate as FlextInfraCodegenQualityGate,
    )
    from flext_infra.codegen.fixer import (
        FlextInfraCodegenFixer as FlextInfraCodegenFixer,
    )
    from flext_infra.codegen.lazy_init import (
        FlextInfraCodegenLazyInit as FlextInfraCodegenLazyInit,
    )
    from flext_infra.codegen.lazy_init_planner import (
        FlextInfraCodegenLazyInitPlanner as FlextInfraCodegenLazyInitPlanner,
    )
    from flext_infra.codegen.pipeline import (
        FlextInfraCodegenPipeline as FlextInfraCodegenPipeline,
    )
    from flext_infra.codegen.py_typed import (
        FlextInfraCodegenPyTyped as FlextInfraCodegenPyTyped,
    )
    from flext_infra.codegen.pyproject_keys import (
        FlextInfraCodegenPyprojectKeys as FlextInfraCodegenPyprojectKeys,
    )
    from flext_infra.codegen.scaffolder import (
        FlextInfraCodegenScaffolder as FlextInfraCodegenScaffolder,
    )
    from flext_infra.codegen.version_file import (
        FlextInfraCodegenVersionFile as FlextInfraCodegenVersionFile,
    )
    from flext_infra.constants import FlextInfraConstants as FlextInfraConstants, c
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionService as FlextInfraDependencyDetectionService,
>>>>>>> Stashed changes
    )
    from flext_infra.fixers.orchestrator import (
        FlextInfraEnforcementFixerOrchestrator as FlextInfraEnforcementFixerOrchestrator,
    )
    from flext_infra.fixers.result import (
        FlextInfraFixersResult as FlextInfraFixersResult,
    )
<<<<<<< Updated upstream
    from flext_infra.fixers.transformer_fixer import (
        FlextInfraTransformerFixerAdapter as FlextInfraTransformerFixerAdapter,
    )
    from flext_infra.models import FlextInfraModels as FlextInfraModels, m as m
    from flext_infra.protocols import (
        FlextInfraProtocols as FlextInfraProtocols,
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
        p as p,
    )
    from flext_infra.settings import FlextInfraSettings as FlextInfraSettings
    from flext_infra.typings import FlextInfraTypes as FlextInfraTypes, t as t
    from flext_infra.utilities import FlextInfraUtilities as FlextInfraUtilities, u as u

_LAZY_IMPORTS = FLEXT_INFRA_LAZY_IMPORTS
_METADATA_EXPORTS = (
=======
    from flext_infra.deps.detector_runtime import (
        FlextInfraDependencyDetectorRuntime as FlextInfraDependencyDetectorRuntime,
    )
    from flext_infra.deps.extra_paths import (
        FlextInfraExtraPathsManager as FlextInfraExtraPathsManager,
    )
    from flext_infra.deps.fix_pyrefly_config import (
        FlextInfraConfigFixer as FlextInfraConfigFixer,
    )
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService as FlextInfraInternalDependencySyncService,
    )
    from flext_infra.deps.modernizer import (
        FlextInfraPyprojectModernizer as FlextInfraPyprojectModernizer,
    )
    from flext_infra.deps.phase_engine import (
        FlextInfraPhaseEngine as FlextInfraPhaseEngine,
    )
    from flext_infra.deps.phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps.phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps.phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps.phases.ensure_mypy import (
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps.phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pytest import (
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps.phases.ensure_ruff import (
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps.phases.inject_comments import (
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector as FlextInfraClassPlacementDetector,
    )
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector as FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector as FlextInfraCyclicImportDetector,
    )
    from flext_infra.detectors.facade_scanner import (
        FlextInfraScanner as FlextInfraScanner,
    )
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector as FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector as FlextInfraImportAliasDetector,
    )
    from flext_infra.detectors.internal_import_detector import (
        FlextInfraInternalImportDetector as FlextInfraInternalImportDetector,
    )
    from flext_infra.detectors.loose_object_detector import (
        FlextInfraLooseObjectDetector as FlextInfraLooseObjectDetector,
    )
    from flext_infra.detectors.manual_protocol_detector import (
        FlextInfraManualProtocolDetector as FlextInfraManualProtocolDetector,
    )
    from flext_infra.detectors.manual_typing_alias_detector import (
        FlextInfraManualTypingAliasDetector as FlextInfraManualTypingAliasDetector,
    )
    from flext_infra.detectors.mro_completeness_detector import (
        FlextInfraMROCompletenessDetector as FlextInfraMROCompletenessDetector,
    )
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector as FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector as FlextInfraRuntimeAliasDetector,
    )
    from flext_infra.detectors.silent_failure_detector import (
        FlextInfraSilentFailureDetector as FlextInfraSilentFailureDetector,
    )
    from flext_infra.docs.auditor import FlextInfraDocAuditor as FlextInfraDocAuditor
    from flext_infra.docs.auditor_mixin import (
        FlextInfraDocAuditorMixin as FlextInfraDocAuditorMixin,
    )
    from flext_infra.docs.base import (
        FlextInfraDocServiceBase as FlextInfraDocServiceBase,
    )
    from flext_infra.docs.builder import FlextInfraDocBuilder as FlextInfraDocBuilder
    from flext_infra.docs.fixer import FlextInfraDocFixer as FlextInfraDocFixer
    from flext_infra.docs.generator import (
        FlextInfraDocGenerator as FlextInfraDocGenerator,
    )
    from flext_infra.docs.validator import (
        FlextInfraDocValidator as FlextInfraDocValidator,
    )
    from flext_infra.gates.abstraction_boundary import (
        FlextInfraAbstractionBoundaryGate as FlextInfraAbstractionBoundaryGate,
    )
    from flext_infra.gates.bandit import FlextInfraBanditGate as FlextInfraBanditGate
    from flext_infra.gates.base_gate import FlextInfraGate as FlextInfraGate
    from flext_infra.gates.loc_cap import FlextInfraLocCapGate as FlextInfraLocCapGate
    from flext_infra.gates.markdown import (
        FlextInfraMarkdownGate as FlextInfraMarkdownGate,
    )
    from flext_infra.gates.mypy import FlextInfraMypyGate as FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate as FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate as FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import (
        FlextInfraRuffFormatGate as FlextInfraRuffFormatGate,
    )
    from flext_infra.gates.ruff_lint import (
        FlextInfraRuffLintGate as FlextInfraRuffLintGate,
    )
    from flext_infra.gates.silent_failure import (
        FlextInfraSilentFailureGate as FlextInfraSilentFailureGate,
    )
    from flext_infra.iteration import (
        FlextInfraUtilitiesIteration as FlextInfraUtilitiesIteration,
    )
    from flext_infra.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer as FlextInfraPythonVersionEnforcer,
    )
    from flext_infra.models import FlextInfraModels as FlextInfraModels, m
    from flext_infra.protocols import FlextInfraProtocols as FlextInfraProtocols, p
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator as FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import (
        FlextInfraRefactorCensus as FlextInfraRefactorCensus,
    )
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer as FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.engine import (
        FlextInfraRefactorEngine as FlextInfraRefactorEngine,
    )
    from flext_infra.refactor.engine_file import (
        FlextInfraClassNestingPostCheckGate as FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor as FlextInfraRefactorFileExecutor,
    )
    from flext_infra.refactor.engine_legacy import (
        FlextInfraRefactorLegacyTextOps as FlextInfraRefactorLegacyTextOps,
    )
    from flext_infra.refactor.engine_text import (
        FlextInfraRefactorTextExecutor as FlextInfraRefactorTextExecutor,
    )
    from flext_infra.refactor.loader import (
        FlextInfraRefactorRuleLoader as FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO as FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.modernize_orchestrator import (
        FlextInfraModernizeOrchestrator as FlextInfraModernizeOrchestrator,
    )
    from flext_infra.refactor.mro_import_rewriter import (
        FlextInfraRefactorMROImportRewriter as FlextInfraRefactorMROImportRewriter,
    )
    from flext_infra.refactor.mro_migration_validator import (
        FlextInfraRefactorMROMigrationValidator as FlextInfraRefactorMROMigrationValidator,
    )
    from flext_infra.refactor.mro_resolver import (
        FlextInfraRefactorMROResolver as FlextInfraRefactorMROResolver,
    )
    from flext_infra.refactor.namespace_enforcer import (
        FlextInfraNamespaceEnforcer as FlextInfraNamespaceEnforcer,
    )
    from flext_infra.refactor.namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin as FlextInfraNamespaceEnforcerPhasesMixin,
    )
    from flext_infra.refactor.orchestrator import (
        FlextInfraRefactorOrchestrator as FlextInfraRefactorOrchestrator,
    )
    from flext_infra.refactor.project_classifier import (
        FlextInfraProjectClassifier as FlextInfraProjectClassifier,
    )
    from flext_infra.refactor.safety import (
        FlextInfraRefactorSafetyManager as FlextInfraRefactorSafetyManager,
    )
    from flext_infra.refactor.scanner import (
        FlextInfraRefactorLooseClassScanner as FlextInfraRefactorLooseClassScanner,
    )
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer as FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.refactor.wrapper_root_namespace import (
        FlextInfraWrapperRootNamespaceRefactor as FlextInfraWrapperRootNamespaceRefactor,
    )
    from flext_infra.release.orchestrator import (
        FlextInfraReleaseOrchestrator as FlextInfraReleaseOrchestrator,
    )
    from flext_infra.release.orchestrator_phases import (
        FlextInfraReleaseOrchestratorPhases as FlextInfraReleaseOrchestratorPhases,
    )
    from flext_infra.settings import FlextInfraSettings as FlextInfraSettings
    from flext_infra.transformers.base import (
        FlextInfraChangeTrackingTransformer as FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer as FlextInfraRopeTransformer,
    )
    from flext_infra.transformers.census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor as FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector as FlextInfraCensusUsageCollector,
    )
    from flext_infra.transformers.class_nesting import (
        FlextInfraRefactorClassNestingTransformer as FlextInfraRefactorClassNestingTransformer,
    )
    from flext_infra.transformers.class_reconstructor import (
        FlextInfraRefactorClassReconstructor as FlextInfraRefactorClassReconstructor,
    )
    from flext_infra.transformers.cli_modernizer import (
        FlextInfraRefactorCliModernizer as FlextInfraRefactorCliModernizer,
    )
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover as FlextInfraRefactorDeprecatedRemover,
    )
    from flext_infra.transformers.helper_consolidation import (
        FlextInfraHelperConsolidationTransformer as FlextInfraHelperConsolidationTransformer,
    )
    from flext_infra.transformers.import_bypass_remover import (
        FlextInfraRefactorImportBypassRemover as FlextInfraRefactorImportBypassRemover,
    )
    from flext_infra.transformers.import_modernizer import (
        FlextInfraRefactorImportModernizer as FlextInfraRefactorImportModernizer,
    )
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer as FlextInfraRefactorLazyImportFixer,
    )
    from flext_infra.transformers.logging_modernizer import (
        FlextInfraRefactorLoggingModernizer as FlextInfraRefactorLoggingModernizer,
    )
    from flext_infra.transformers.mro_remover import (
        FlextInfraRefactorMRORemover as FlextInfraRefactorMRORemover,
    )
    from flext_infra.transformers.mro_symbol_propagator import (
        FlextInfraRefactorMROSymbolPropagator as FlextInfraRefactorMROSymbolPropagator,
    )
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer as FlextInfraNestedClassPropagationTransformer,
    )
    from flext_infra.transformers.pattern_modernizer import (
        FlextInfraRefactorPatternModernizer as FlextInfraRefactorPatternModernizer,
    )
    from flext_infra.transformers.pydantic_modernizer import (
        FlextInfraRefactorPydanticModernizer as FlextInfraRefactorPydanticModernizer,
    )
    from flext_infra.transformers.result_di_modernizer import (
        FlextInfraRefactorResultDiModernizer as FlextInfraRefactorResultDiModernizer,
    )
    from flext_infra.transformers.signature_propagator import (
        FlextInfraRefactorSignaturePropagator as FlextInfraRefactorSignaturePropagator,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator as FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.tests_modernizer import (
        FlextInfraRefactorTestsModernizer as FlextInfraRefactorTestsModernizer,
    )
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer as FlextInfraTransformerTier0ImportFixer,
    )
    from flext_infra.transformers.typing_unifier import (
        FlextInfraRefactorTypingUnifier as FlextInfraRefactorTypingUnifier,
    )
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor as FlextInfraViolationCensusVisitor,
    )
    from flext_infra.typings import FlextInfraTypes as FlextInfraTypes, t
    from flext_infra.utilities import FlextInfraUtilities as FlextInfraUtilities, u
    from flext_infra.validate.basemk_validator import (
        FlextInfraBaseMkValidator as FlextInfraBaseMkValidator,
    )
    from flext_infra.validate.fresh_import import (
        FlextInfraValidateFreshImport as FlextInfraValidateFreshImport,
    )
    from flext_infra.validate.gate_contract import (
        FlextInfraGateContractValidator as FlextInfraGateContractValidator,
    )
    from flext_infra.validate.gate_contract_checks import (
        FlextInfraGateContractChecksMixin as FlextInfraGateContractChecksMixin,
    )
    from flext_infra.validate.gate_contract_content import (
        FlextInfraGateContractContentMixin as FlextInfraGateContractContentMixin,
    )
    from flext_infra.validate.gate_contract_models import (
        FlextInfraGateContractModels as FlextInfraGateContractModels,
    )
    from flext_infra.validate.gate_contract_report import (
        FlextInfraGateContractReportMixin as FlextInfraGateContractReportMixin,
    )
    from flext_infra.validate.gate_contract_scan import (
        FlextInfraGateContractScanMixin as FlextInfraGateContractScanMixin,
    )
    from flext_infra.validate.import_cycles import (
        FlextInfraValidateImportCycles as FlextInfraValidateImportCycles,
    )
    from flext_infra.validate.inventory import (
        FlextInfraInventoryService as FlextInfraInventoryService,
    )
    from flext_infra.validate.lazy_map_freshness import (
        FlextInfraValidateLazyMapFreshness as FlextInfraValidateLazyMapFreshness,
    )
    from flext_infra.validate.loc_delta import (
        FlextInfraLocDeltaValidator as FlextInfraLocDeltaValidator,
    )
    from flext_infra.validate.manual_command import (
        FlextInfraManualCommandValidator as FlextInfraManualCommandValidator,
    )
    from flext_infra.validate.metadata_discipline import (
        FlextInfraValidateMetadataDiscipline as FlextInfraValidateMetadataDiscipline,
    )
    from flext_infra.validate.namespace_rules import (
        FlextInfraNamespaceRules as FlextInfraNamespaceRules,
    )
    from flext_infra.validate.namespace_validator import (
        FlextInfraNamespaceValidator as FlextInfraNamespaceValidator,
    )
    from flext_infra.validate.pytest_diag import (
        FlextInfraPytestDiagExtractor as FlextInfraPytestDiagExtractor,
    )
    from flext_infra.validate.scanner import (
        FlextInfraTextPatternScanner as FlextInfraTextPatternScanner,
    )
    from flext_infra.validate.silent_failure import (
        FlextInfraSilentFailureValidator as FlextInfraSilentFailureValidator,
    )
    from flext_infra.validate.skill_validator import (
        FlextInfraSkillValidator as FlextInfraSkillValidator,
    )
    from flext_infra.validate.stub_chain import (
        FlextInfraStubSupplyChain as FlextInfraStubSupplyChain,
    )
    from flext_infra.validate.tier_whitelist import (
        FlextInfraValidateTierWhitelist as FlextInfraValidateTierWhitelist,
    )
    from flext_infra.workspace.base import (
        FlextInfraWorkspaceGeneratorBase as FlextInfraWorkspaceGeneratorBase,
    )
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector as FlextInfraWorkspaceDetector,
    )
    from flext_infra.workspace.migrator import (
        FlextInfraProjectMigrator as FlextInfraProjectMigrator,
    )
    from flext_infra.workspace.orchestrator import (
        FlextInfraOrchestratorService as FlextInfraOrchestratorService,
    )
    from flext_infra.workspace.project_makefile import (
        FlextInfraProjectMakefileUpdater as FlextInfraProjectMakefileUpdater,
    )
    from flext_infra.workspace.rope import (
        FlextInfraRopeWorkspace as FlextInfraRopeWorkspace,
    )
    from flext_infra.workspace.sandbox_orchestrator import (
        FlextInfraSandboxOrchestrator as FlextInfraSandboxOrchestrator,
    )
    from flext_infra.workspace.sync import (
        FlextInfraSyncService as FlextInfraSyncService,
    )
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator as FlextInfraWorkspaceMakefileGenerator,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "._constants",
        "._models",
        "._protocols",
        "._typings",
        "._utilities",
        ".basemk",
        ".check",
        ".codegen",
        ".deps",
        ".detectors",
        ".docs",
        ".gates",
        ".maintenance",
        ".refactor",
        ".release",
        ".transformers",
        ".validate",
        ".workspace",
    ),
    build_lazy_import_map(
        {
            "._constants.base": ("FlextInfraConstantsBase",),
            "._constants.basemk": ("FlextInfraConstantsBasemk",),
            "._constants.census": ("FlextInfraConstantsCensus",),
            "._constants.check": ("FlextInfraConstantsCheck",),
            "._constants.codegen": ("FlextInfraConstantsCodegen",),
            "._constants.deps": ("FlextInfraConstantsDeps",),
            "._constants.docs": ("FlextInfraConstantsDocs",),
            "._constants.github": ("FlextInfraConstantsGithub",),
            "._constants.make": ("FlextInfraConstantsMake",),
            "._constants.namespace": ("FlextInfraConstantsNamespace",),
            "._constants.refactor": ("FlextInfraConstantsRefactor",),
            "._constants.release": ("FlextInfraConstantsRelease",),
            "._constants.rope": ("FlextInfraConstantsRope",),
            "._constants.source_code": ("FlextInfraConstantsSourceCode",),
            "._constants.validate": ("FlextInfraConstantsSharedInfra",),
            "._constants.workspace": ("FlextInfraConstantsWorkspace",),
            "._models.base": ("FlextInfraModelsBase",),
            "._models.basemk": ("FlextInfraModelsBasemk",),
            "._models.census": ("FlextInfraModelsCensus",),
            "._models.check": ("FlextInfraModelsCheck",),
            "._models.codegen": ("FlextInfraModelsCodegen",),
            "._models.deps": ("FlextInfraModelsDeps",),
            "._models.deps_tool_config": ("FlextInfraModelsDepsToolSettings",),
            "._models.deps_tool_config_linters": (
                "FlextInfraModelsDepsToolConfigLinters",
            ),
            "._models.deps_tool_config_type_checkers": (
                "FlextInfraModelsDepsToolConfigTypeCheckers",
            ),
            "._models.docs": ("FlextInfraModelsDocs",),
            "._models.engine": ("FlextInfraModelsEngine",),
            "._models.engine_ops": ("FlextInfraModelsEngineOperation",),
            "._models.gates": ("FlextInfraModelsGates",),
            "._models.github": ("FlextInfraModelsGithub",),
            "._models.mixins": ("FlextInfraModelsMixins",),
            "._models.mro_scan": ("FlextInfraModelsMroScan",),
            "._models.refactor": ("FlextInfraModelsRefactor",),
            "._models.refactor_ast_grep": ("FlextInfraModelsRefactorGrep",),
            "._models.refactor_census": ("FlextInfraModelsRefactorCensus",),
            "._models.refactor_namespace_enforcer": (
                "FlextInfraModelsNamespaceEnforcer",
            ),
            "._models.refactor_violations": ("FlextInfraModelsRefactorViolations",),
            "._models.release": ("FlextInfraModelsRelease",),
            "._models.rope": ("FlextInfraModelsRope",),
            "._models.scan": ("FlextInfraModelsScan",),
            "._models.validate": ("FlextInfraModelsCore",),
            "._models.workspace": ("FlextInfraModelsWorkspace",),
            "._protocols.base": ("FlextInfraProtocolsBase",),
            "._protocols.check": ("FlextInfraProtocolsCheck",),
            "._protocols.rope": ("FlextInfraProtocolsRope",),
            "._typings.adapters": ("FlextInfraTypesAdapters",),
            "._typings.base": ("FlextInfraTypesBase",),
            "._typings.rope": ("FlextInfraTypesRope",),
            "._utilities._docs_audit_detectors": (
                "FlextInfraUtilitiesDocsAuditDetectorsMixin",
            ),
            "._utilities._docs_scope_build": (
                "FlextInfraUtilitiesDocsScopeBuildMixin",
            ),
            "._utilities._docs_scope_selection": (
                "FlextInfraUtilitiesDocsScopeSelectionMixin",
            ),
            "._utilities._github_pr_single": (
                "FlextInfraUtilitiesGithubPrSingleMixin",
            ),
            "._utilities._github_sync": ("FlextInfraUtilitiesGithubSyncMixin",),
            "._utilities._rope_bracket_balance": (
                "FlextInfraUtilitiesRopeBracketBalanceMixin",
            ),
            "._utilities._rope_core_pymodule": (
                "FlextInfraUtilitiesRopeCorePyModuleMixin",
            ),
            "._utilities._rope_core_resources": (
                "FlextInfraUtilitiesRopeCoreResourcesMixin",
            ),
            "._utilities._rope_method_order": (
                "FlextInfraUtilitiesRopeMethodOrderMixin",
            ),
            "._utilities.base": ("FlextInfraUtilitiesBase",),
            "._utilities.census": ("FlextInfraUtilitiesRefactorCensus",),
            "._utilities.codegen": ("FlextInfraUtilitiesCodegen",),
            "._utilities.dependencies": ("FlextInfraUtilitiesDependencies",),
            "._utilities.deps_path_sync": ("FlextInfraUtilitiesDependencyPathSync",),
            "._utilities.deps_repos": ("FlextInfraInternalSyncRepoMixin",),
            "._utilities.discovery": ("FlextInfraUtilitiesDiscovery",),
            "._utilities.docs": ("FlextInfraUtilitiesDocs",),
            "._utilities.docs_api": ("FlextInfraUtilitiesDocsApi",),
            "._utilities.docs_audit": ("FlextInfraUtilitiesDocsAudit",),
            "._utilities.docs_build": ("FlextInfraUtilitiesDocsBuild",),
            "._utilities.docs_contract": ("FlextInfraUtilitiesDocsContract",),
            "._utilities.docs_fix": ("FlextInfraUtilitiesDocsFix",),
            "._utilities.docs_generate": ("FlextInfraUtilitiesDocsGenerate",),
            "._utilities.docs_render": ("FlextInfraUtilitiesDocsRender",),
            "._utilities.docs_scope": ("FlextInfraUtilitiesDocsScope",),
            "._utilities.docs_validate": ("FlextInfraUtilitiesDocsValidate",),
            "._utilities.engine": ("FlextInfraUtilitiesRefactorEngine",),
            "._utilities.git_scope": ("FlextInfraUtilitiesGitScope",),
            "._utilities.github": ("FlextInfraUtilitiesGithub",),
            "._utilities.github_pr": ("FlextInfraUtilitiesGithubPr",),
            "._utilities.log_parser": ("FlextInfraUtilitiesLogParser",),
            "._utilities.mro_scan": ("FlextInfraUtilitiesRefactorMroScan",),
            "._utilities.mro_scan_catalog": ("FlextInfraUtilitiesMroScanCatalog",),
            "._utilities.mro_scan_source": ("FlextInfraUtilitiesMroScanSource",),
            "._utilities.namespace": ("FlextInfraUtilitiesCodegenNamespace",),
            "._utilities.namespace_analysis": (
                "FlextInfraUtilitiesRefactorNamespaceMro",
            ),
            "._utilities.namespace_common": (
                "FlextInfraUtilitiesRefactorNamespaceCommon",
            ),
            "._utilities.namespace_config": ("FlextInfraUtilitiesNamespaceConfig",),
            "._utilities.namespace_facades": (
                "FlextInfraUtilitiesRefactorNamespaceFacades",
            ),
            "._utilities.namespace_moves": (
                "FlextInfraUtilitiesRefactorNamespaceMoves",
            ),
            "._utilities.policy": ("FlextInfraUtilitiesRefactorPolicy",),
            "._utilities.project_discovery": ("FlextInfraUtilitiesProjectDiscovery",),
            "._utilities.protected_edit": ("FlextInfraUtilitiesProtectedEdit",),
            "._utilities.protected_edit_apply": (
                "FlextInfraUtilitiesProtectedEditApply",
            ),
            "._utilities.protected_edit_linting": (
                "FlextInfraUtilitiesProtectedEditLinting",
            ),
            "._utilities.protected_edit_preview": (
                "FlextInfraUtilitiesProtectedEditPreview",
            ),
            "._utilities.protected_edit_writes": (
                "FlextInfraUtilitiesProtectedEditWrites",
            ),
            "._utilities.pyproject": ("FlextInfraUtilitiesPyproject",),
            "._utilities.refactor": ("FlextInfraUtilitiesRefactor",),
            "._utilities.release": ("FlextInfraUtilitiesRelease",),
            "._utilities.rope_analysis": ("FlextInfraUtilitiesRopeAnalysis",),
            "._utilities.rope_analysis_introspection": (
                "FlextInfraUtilitiesRopeAnalysisIntrospection",
            ),
            "._utilities.rope_analysis_workspace": (
                "FlextInfraUtilitiesRopeAnalysisWorkspace",
            ),
            "._utilities.rope_core": ("FlextInfraUtilitiesRopeCore",),
            "._utilities.rope_helpers": ("FlextInfraUtilitiesRopeHelpers",),
            "._utilities.rope_imports": ("FlextInfraUtilitiesRopeImports",),
            "._utilities.rope_inventory": ("FlextInfraUtilitiesRopeInventory",),
            "._utilities.rope_module_patch": ("FlextInfraUtilitiesRopeModulePatch",),
            "._utilities.rope_mro_transform": ("FlextInfraUtilitiesRopeMroTransform",),
            "._utilities.rope_pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
            "._utilities.rope_source": ("FlextInfraUtilitiesRopeSource",),
            "._utilities.safety": ("FlextInfraUtilitiesSafety",),
            "._utilities.snapshot": ("FlextInfraUtilitiesSnapshot",),
            "._utilities.versioning": ("FlextInfraUtilitiesVersioning",),
            ".api": (
                "FlextInfra",
                "infra",
            ),
            ".base": (
                "FlextInfraProjectSelectionServiceBase",
                "FlextInfraServiceBase",
                "s",
            ),
            ".basemk.engine": ("FlextInfraBaseMkTemplateEngine",),
            ".basemk.generator": ("FlextInfraBaseMkGenerator",),
            ".check.workspace_check": ("FlextInfraWorkspaceChecker",),
            ".check.workspace_check_gates": (
                "FlextInfraGateRegistry",
                "FlextInfraWorkspaceCheckGatesMixin",
            ),
            ".cli": (
                "FlextInfraCli",
                "main",
            ),
            ".codegen.census": ("FlextInfraCodegenCensus",),
            ".codegen.codegen_generation": ("FlextInfraCodegenGeneration",),
            ".codegen.consolidator": ("FlextInfraCodegenConsolidator",),
            ".codegen.constants_quality_gate": ("FlextInfraCodegenQualityGate",),
            ".codegen.fixer": ("FlextInfraCodegenFixer",),
            ".codegen.lazy_init": ("FlextInfraCodegenLazyInit",),
            ".codegen.lazy_init_planner": ("FlextInfraCodegenLazyInitPlanner",),
            ".codegen.pipeline": ("FlextInfraCodegenPipeline",),
            ".codegen.py_typed": ("FlextInfraCodegenPyTyped",),
            ".codegen.pyproject_keys": ("FlextInfraCodegenPyprojectKeys",),
            ".codegen.scaffolder": ("FlextInfraCodegenScaffolder",),
            ".codegen.version_file": ("FlextInfraCodegenVersionFile",),
            ".constants": (
                "FlextInfraConstants",
                "c",
            ),
            ".deps.detection": ("FlextInfraDependencyDetectionService",),
            ".deps.detection_analysis": ("FlextInfraDependencyDetectionAnalysis",),
            ".deps.detector": ("FlextInfraRuntimeDevDependencyDetector",),
            ".deps.detector_runtime": ("FlextInfraDependencyDetectorRuntime",),
            ".deps.extra_paths": ("FlextInfraExtraPathsManager",),
            ".deps.fix_pyrefly_config": ("FlextInfraConfigFixer",),
            ".deps.internal_sync": ("FlextInfraInternalDependencySyncService",),
            ".deps.modernizer": ("FlextInfraPyprojectModernizer",),
            ".deps.phase_engine": ("FlextInfraPhaseEngine",),
            ".deps.phases.consolidate_groups": ("FlextInfraConsolidateGroupsPhase",),
            ".deps.phases.ensure_coverage": ("FlextInfraEnsureCoverageConfigPhase",),
            ".deps.phases.ensure_formatting": (
                "FlextInfraEnsureFormattingToolingPhase",
            ),
            ".deps.phases.ensure_mypy": ("FlextInfraEnsureMypyConfigPhase",),
            ".deps.phases.ensure_namespace": ("FlextInfraEnsureNamespaceToolingPhase",),
            ".deps.phases.ensure_pydantic_mypy": (
                "FlextInfraEnsurePydanticMypyConfigPhase",
            ),
            ".deps.phases.ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
            ".deps.phases.ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
            ".deps.phases.ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
            ".deps.phases.ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
            ".deps.phases.inject_comments": ("FlextInfraInjectCommentsPhase",),
            ".detectors.class_placement_detector": (
                "FlextInfraClassPlacementDetector",
            ),
            ".detectors.compatibility_alias_detector": (
                "FlextInfraCompatibilityAliasDetector",
            ),
            ".detectors.cyclic_import_detector": ("FlextInfraCyclicImportDetector",),
            ".detectors.facade_scanner": ("FlextInfraScanner",),
            ".detectors.future_annotations_detector": (
                "FlextInfraFutureAnnotationsDetector",
            ),
            ".detectors.import_alias_detector": ("FlextInfraImportAliasDetector",),
            ".detectors.internal_import_detector": (
                "FlextInfraInternalImportDetector",
            ),
            ".detectors.loose_object_detector": ("FlextInfraLooseObjectDetector",),
            ".detectors.manual_protocol_detector": (
                "FlextInfraManualProtocolDetector",
            ),
            ".detectors.manual_typing_alias_detector": (
                "FlextInfraManualTypingAliasDetector",
            ),
            ".detectors.mro_completeness_detector": (
                "FlextInfraMROCompletenessDetector",
            ),
            ".detectors.namespace_source_detector": (
                "FlextInfraNamespaceSourceDetector",
            ),
            ".detectors.runtime_alias_detector": ("FlextInfraRuntimeAliasDetector",),
            ".detectors.silent_failure_detector": ("FlextInfraSilentFailureDetector",),
            ".docs.auditor": ("FlextInfraDocAuditor",),
            ".docs.auditor_mixin": ("FlextInfraDocAuditorMixin",),
            ".docs.base": ("FlextInfraDocServiceBase",),
            ".docs.builder": ("FlextInfraDocBuilder",),
            ".docs.fixer": ("FlextInfraDocFixer",),
            ".docs.generator": ("FlextInfraDocGenerator",),
            ".docs.validator": ("FlextInfraDocValidator",),
            ".gates.abstraction_boundary": ("FlextInfraAbstractionBoundaryGate",),
            ".gates.bandit": ("FlextInfraBanditGate",),
            ".gates.base_gate": ("FlextInfraGate",),
            ".gates.loc_cap": ("FlextInfraLocCapGate",),
            ".gates.markdown": ("FlextInfraMarkdownGate",),
            ".gates.mypy": ("FlextInfraMypyGate",),
            ".gates.pyrefly": ("FlextInfraPyreflyGate",),
            ".gates.pyright": ("FlextInfraPyrightGate",),
            ".gates.ruff_format": ("FlextInfraRuffFormatGate",),
            ".gates.ruff_lint": ("FlextInfraRuffLintGate",),
            ".gates.silent_failure": ("FlextInfraSilentFailureGate",),
            ".iteration": ("FlextInfraUtilitiesIteration",),
            ".maintenance.python_version": ("FlextInfraPythonVersionEnforcer",),
            ".models": (
                "FlextInfraModels",
                "m",
            ),
            ".protocols": (
                "FlextInfraProtocols",
                "p",
            ),
            ".refactor.accessor_migration": (
                "FlextInfraAccessorMigrationOrchestrator",
            ),
            ".refactor.census": ("FlextInfraRefactorCensus",),
            ".refactor.class_nesting_analyzer": (
                "FlextInfraRefactorClassNestingAnalyzer",
            ),
            ".refactor.engine": ("FlextInfraRefactorEngine",),
            ".refactor.engine_file": (
                "FlextInfraClassNestingPostCheckGate",
                "FlextInfraRefactorFileExecutor",
            ),
            ".refactor.engine_legacy": ("FlextInfraRefactorLegacyTextOps",),
            ".refactor.engine_text": ("FlextInfraRefactorTextExecutor",),
            ".refactor.loader": ("FlextInfraRefactorRuleLoader",),
            ".refactor.migrate_to_class_mro": ("FlextInfraRefactorMigrateToClassMRO",),
            ".refactor.modernize_orchestrator": ("FlextInfraModernizeOrchestrator",),
            ".refactor.mro_import_rewriter": ("FlextInfraRefactorMROImportRewriter",),
            ".refactor.mro_migration_validator": (
                "FlextInfraRefactorMROMigrationValidator",
            ),
            ".refactor.mro_resolver": ("FlextInfraRefactorMROResolver",),
            ".refactor.namespace_enforcer": ("FlextInfraNamespaceEnforcer",),
            ".refactor.namespace_enforcer_phases": (
                "FlextInfraNamespaceEnforcerPhasesMixin",
            ),
            ".refactor.orchestrator": ("FlextInfraRefactorOrchestrator",),
            ".refactor.project_classifier": ("FlextInfraProjectClassifier",),
            ".refactor.safety": ("FlextInfraRefactorSafetyManager",),
            ".refactor.scanner": ("FlextInfraRefactorLooseClassScanner",),
            ".refactor.violation_analyzer": ("FlextInfraRefactorViolationAnalyzer",),
            ".refactor.wrapper_root_namespace": (
                "FlextInfraWrapperRootNamespaceRefactor",
            ),
            ".release.orchestrator": ("FlextInfraReleaseOrchestrator",),
            ".release.orchestrator_phases": ("FlextInfraReleaseOrchestratorPhases",),
            ".settings": ("FlextInfraSettings",),
            ".transformers.base": (
                "FlextInfraChangeTrackingTransformer",
                "FlextInfraRopeTransformer",
            ),
            ".transformers.census_visitors": (
                "FlextInfraCensusImportDiscoveryVisitor",
                "FlextInfraCensusUsageCollector",
            ),
            ".transformers.class_nesting": (
                "FlextInfraRefactorClassNestingTransformer",
            ),
            ".transformers.class_reconstructor": (
                "FlextInfraRefactorClassReconstructor",
            ),
            ".transformers.cli_modernizer": ("FlextInfraRefactorCliModernizer",),
            ".transformers.deprecated_remover": (
                "FlextInfraRefactorDeprecatedRemover",
            ),
            ".transformers.helper_consolidation": (
                "FlextInfraHelperConsolidationTransformer",
            ),
            ".transformers.import_bypass_remover": (
                "FlextInfraRefactorImportBypassRemover",
            ),
            ".transformers.import_modernizer": ("FlextInfraRefactorImportModernizer",),
            ".transformers.lazy_import_fixer": ("FlextInfraRefactorLazyImportFixer",),
            ".transformers.logging_modernizer": (
                "FlextInfraRefactorLoggingModernizer",
            ),
            ".transformers.mro_remover": ("FlextInfraRefactorMRORemover",),
            ".transformers.mro_symbol_propagator": (
                "FlextInfraRefactorMROSymbolPropagator",
            ),
            ".transformers.nested_class_propagation": (
                "FlextInfraNestedClassPropagationTransformer",
            ),
            ".transformers.pattern_modernizer": (
                "FlextInfraRefactorPatternModernizer",
            ),
            ".transformers.pydantic_modernizer": (
                "FlextInfraRefactorPydanticModernizer",
            ),
            ".transformers.result_di_modernizer": (
                "FlextInfraRefactorResultDiModernizer",
            ),
            ".transformers.signature_propagator": (
                "FlextInfraRefactorSignaturePropagator",
            ),
            ".transformers.symbol_propagator": ("FlextInfraRefactorSymbolPropagator",),
            ".transformers.tests_modernizer": ("FlextInfraRefactorTestsModernizer",),
            ".transformers.tier0_import_fixer": (
                "FlextInfraTransformerTier0ImportFixer",
            ),
            ".transformers.typing_unifier": ("FlextInfraRefactorTypingUnifier",),
            ".transformers.violation_census_visitor": (
                "FlextInfraViolationCensusVisitor",
            ),
            ".typings": (
                "FlextInfraTypes",
                "t",
            ),
            ".utilities": (
                "FlextInfraUtilities",
                "u",
            ),
            ".validate.basemk_validator": ("FlextInfraBaseMkValidator",),
            ".validate.fresh_import": ("FlextInfraValidateFreshImport",),
            ".validate.gate_contract": ("FlextInfraGateContractValidator",),
            ".validate.gate_contract_checks": ("FlextInfraGateContractChecksMixin",),
            ".validate.gate_contract_content": ("FlextInfraGateContractContentMixin",),
            ".validate.gate_contract_models": ("FlextInfraGateContractModels",),
            ".validate.gate_contract_report": ("FlextInfraGateContractReportMixin",),
            ".validate.gate_contract_scan": ("FlextInfraGateContractScanMixin",),
            ".validate.import_cycles": ("FlextInfraValidateImportCycles",),
            ".validate.inventory": ("FlextInfraInventoryService",),
            ".validate.lazy_map_freshness": ("FlextInfraValidateLazyMapFreshness",),
            ".validate.loc_delta": ("FlextInfraLocDeltaValidator",),
            ".validate.manual_command": ("FlextInfraManualCommandValidator",),
            ".validate.metadata_discipline": ("FlextInfraValidateMetadataDiscipline",),
            ".validate.namespace_rules": ("FlextInfraNamespaceRules",),
            ".validate.namespace_validator": ("FlextInfraNamespaceValidator",),
            ".validate.pytest_diag": ("FlextInfraPytestDiagExtractor",),
            ".validate.scanner": ("FlextInfraTextPatternScanner",),
            ".validate.silent_failure": ("FlextInfraSilentFailureValidator",),
            ".validate.skill_validator": ("FlextInfraSkillValidator",),
            ".validate.stub_chain": ("FlextInfraStubSupplyChain",),
            ".validate.tier_whitelist": ("FlextInfraValidateTierWhitelist",),
            ".workspace.base": ("FlextInfraWorkspaceGeneratorBase",),
            ".workspace.detector": ("FlextInfraWorkspaceDetector",),
            ".workspace.migrator": ("FlextInfraProjectMigrator",),
            ".workspace.orchestrator": ("FlextInfraOrchestratorService",),
            ".workspace.project_makefile": ("FlextInfraProjectMakefileUpdater",),
            ".workspace.rope": ("FlextInfraRopeWorkspace",),
            ".workspace.sandbox_orchestrator": ("FlextInfraSandboxOrchestrator",),
            ".workspace.sync": ("FlextInfraSyncService",),
            ".workspace.workspace_makefile": ("FlextInfraWorkspaceMakefileGenerator",),
            "flext_core": (
                "d",
                "e",
                "h",
                "r",
                "x",
            ),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "path_sync",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name=__name__,
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    [
        "__author__",
        "__author_email__",
        "__description__",
        "__license__",
        "__title__",
        "__url__",
        "__version__",
        "__version_info__",
    ],
)

__all__: list[str] = [
    "FlextInfra",
    "FlextInfraAbstractionBoundaryGate",
    "FlextInfraAccessorMigrationOrchestrator",
    "FlextInfraBanditGate",
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
    "FlextInfraBaseMkValidator",
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraClassNestingPostCheckGate",
    "FlextInfraClassPlacementDetector",
    "FlextInfraCli",
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenLazyInitPlanner",
    "FlextInfraCodegenPipeline",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenPyprojectKeys",
    "FlextInfraCodegenQualityGate",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenVersionFile",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraConstants",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDependencyDetectionAnalysis",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDocAuditor",
    "FlextInfraDocAuditorMixin",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocServiceBase",
    "FlextInfraDocValidator",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraFutureAnnotationsDetector",
    "FlextInfraGate",
    "FlextInfraGateContractChecksMixin",
    "FlextInfraGateContractContentMixin",
    "FlextInfraGateContractModels",
    "FlextInfraGateContractReportMixin",
    "FlextInfraGateContractScanMixin",
    "FlextInfraGateContractValidator",
    "FlextInfraGateRegistry",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraImportAliasDetector",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraInternalImportDetector",
    "FlextInfraInventoryService",
    "FlextInfraLocCapGate",
    "FlextInfraLocDeltaValidator",
    "FlextInfraLooseObjectDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraManualCommandValidator",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraMarkdownGate",
    "FlextInfraModels",
    "FlextInfraModernizeOrchestrator",
    "FlextInfraMypyGate",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerPhasesMixin",
    "FlextInfraNamespaceRules",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraNamespaceValidator",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraOrchestratorService",
    "FlextInfraPhaseEngine",
    "FlextInfraProjectClassifier",
    "FlextInfraProjectMakefileUpdater",
    "FlextInfraProjectMigrator",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorCliModernizer",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorFileExecutor",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorLegacyTextOps",
    "FlextInfraRefactorLoggingModernizer",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorOrchestrator",
    "FlextInfraRefactorPatternModernizer",
    "FlextInfraRefactorPydanticModernizer",
    "FlextInfraRefactorResultDiModernizer",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTestsModernizer",
    "FlextInfraRefactorTextExecutor",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraRefactorViolationAnalyzer",
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseOrchestratorPhases",
    "FlextInfraRopeTransformer",
    "FlextInfraRopeWorkspace",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "FlextInfraRuntimeAliasDetector",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraSandboxOrchestrator",
    "FlextInfraScanner",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraSilentFailureDetector",
    "FlextInfraSilentFailureGate",
    "FlextInfraSilentFailureValidator",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraSyncService",
    "FlextInfraTextPatternScanner",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "FlextInfraUtilitiesIteration",
    "FlextInfraValidateFreshImport",
    "FlextInfraValidateImportCycles",
    "FlextInfraValidateLazyMapFreshness",
    "FlextInfraValidateMetadataDiscipline",
    "FlextInfraValidateTierWhitelist",
    "FlextInfraViolationCensusVisitor",
    "FlextInfraWorkspaceCheckGatesMixin",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceGeneratorBase",
    "FlextInfraWorkspaceMakefileGenerator",
    "FlextInfraWrapperRootNamespaceRefactor",
>>>>>>> Stashed changes
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
)
_PUBLIC_EXPORTS = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraEnforcementFixerOrchestrator",
    "FlextInfraFixerAdapter",
    "FlextInfraFixersResult",
    "FlextInfraGateFixerAdapter",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraTransformerFixerAdapter",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    *_METADATA_EXPORTS,
    "c",
    "d",
    "e",
    "h",
    "infra",
    "m",
    "main",
    "p",
    "r",
    "s",
    "t",
    "u",
    "x",
)
_PUBLISHED_NAMES = frozenset({*_LAZY_IMPORTS, *_METADATA_EXPORTS})
_ROOT_EXPORTS_DRIFT_ERROR = "flext_infra root exports drift from FLEXT_INFRA_LAZY_IMPORTS"
if not frozenset(_PUBLIC_EXPORTS) <= _PUBLISHED_NAMES:
    raise RuntimeError(_ROOT_EXPORTS_DRIFT_ERROR)

install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
