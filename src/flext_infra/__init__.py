# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Flext infra package."""

from __future__ import annotations

import typing as _t

from flext_core.decorators import FlextDecorators as d
from flext_core.exceptions import FlextExceptions as e
from flext_core.handlers import FlextHandlers as h
from flext_core.lazy import install_lazy_exports, merge_lazy_imports
from flext_core.mixins import FlextMixins as x
from flext_core.result import FlextResult as r
from flext_core.service import FlextService as s
from flext_infra.__version__ import *
from flext_infra.__version__ import (
    FlextInfraVersion,
    __author__,
    __author_email__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)
from flext_infra._constants.base import FlextInfraConstantsBase
from flext_infra._constants.census import FlextInfraConstantsCensus
from flext_infra._constants.make import FlextInfraConstantsMake
from flext_infra._constants.rope import FlextInfraConstantsRope
from flext_infra._constants.source_code import FlextInfraConstantsSourceCode
from flext_infra._models.base import FlextInfraModelsBase
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.cli_inputs import FlextInfraModelsCliInputs
from flext_infra._models.cli_inputs_codegen import FlextInfraModelsCliInputsCodegen
from flext_infra._models.cli_inputs_ops import FlextInfraModelsCliInputsOps
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.scan import FlextInfraModelsScan
from flext_infra._protocols.base import FlextInfraProtocolsBase
from flext_infra._protocols.rope import FlextInfraProtocolsRope
from flext_infra._typings.adapters import FlextInfraTypesAdapters
from flext_infra._typings.base import FlextInfraTypesBase
from flext_infra._typings.rope import FlextInfraTypesRope
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.cli import FlextInfraUtilitiesCli
from flext_infra._utilities.cli_shared import FlextInfraUtilitiesCliShared
from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand
from flext_infra._utilities.codegen_constant_analysis import (
    FlextInfraUtilitiesCodegenConstantAnalysis,
)
from flext_infra._utilities.codegen_constant_detection import (
    FlextInfraUtilitiesCodegenConstantDetection,
)
from flext_infra._utilities.codegen_constant_transformation import (
    FlextInfraUtilitiesCodegenConstantTransformation,
)
from flext_infra._utilities.codegen_execution import (
    FlextInfraUtilitiesCodegenExecution,
)
from flext_infra._utilities.codegen_governance import (
    FlextInfraUtilitiesCodegenGovernance,
)
from flext_infra._utilities.codegen_import_cycles import (
    FlextInfraUtilitiesCodegenImportCycles,
)
from flext_infra._utilities.codegen_lazy_aliases import (
    FlextInfraUtilitiesCodegenLazyAliases,
)
from flext_infra._utilities.codegen_lazy_merging import (
    FlextInfraUtilitiesCodegenLazyMerging,
)
from flext_infra._utilities.codegen_lazy_scanning import (
    FlextInfraUtilitiesCodegenLazyScanning,
)
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.discovery_scanning import (
    FlextInfraUtilitiesDiscoveryScanning,
)
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra._utilities.github import FlextInfraUtilitiesGithub
from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr
from flext_infra._utilities.io import FlextInfraUtilitiesIo
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
from flext_infra._utilities.output import FlextInfraUtilitiesOutput, output
from flext_infra._utilities.output_reporting import (
    FlextInfraUtilitiesOutputReporting,
)
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra._utilities.paths import FlextInfraUtilitiesPaths
from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
from flext_infra._utilities.release import FlextInfraUtilitiesRelease
from flext_infra._utilities.reporting import FlextInfraUtilitiesReporting
from flext_infra._utilities.rope import FlextInfraUtilitiesRope
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
from flext_infra._utilities.rule_helpers import FlextInfraUtilitiesRuleHelpers
from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
from flext_infra._utilities.selection import FlextInfraUtilitiesSelection
from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess
from flext_infra._utilities.templates import FlextInfraUtilitiesTemplates
from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
from flext_infra._utilities.toml import FlextInfraUtilitiesToml
from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse
from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml
from flext_infra.basemk._constants import FlextInfraBasemkConstants
from flext_infra.basemk._models import FlextInfraBasemkModels
from flext_infra.basemk.cli import FlextInfraCliBasemk
from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.check._constants import FlextInfraCheckConstants
from flext_infra.check._models import FlextInfraCheckModels
from flext_infra.check._workspace_check_gates import (
    FlextInfraWorkspaceCheckGatesMixin,
)
from flext_infra.check.cli import FlextInfraCliCheck
from flext_infra.check.services import (
    FlextInfraConfigFixer,
    FlextInfraWorkspaceChecker,
)
from flext_infra.check.workspace_check import build_parser, run_cli
from flext_infra.check.workspace_check_cli import FlextInfraWorkspaceCheckerCli
from flext_infra.cli import FlextInfraCli, main
from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration
from flext_infra.codegen._codegen_generation_helpers import (
    _build_lazy_entries,
    _collapse_to_children,
    _emit_type_checking_module,
    _format_import,
    _format_module_alias_import,
    _format_type_checking_module_alias_import,
    _group_imports,
    _has_flext_types,
    _is_local_module,
)
from flext_infra.codegen._codegen_snapshot import FlextInfraCodegenSnapshot
from flext_infra.codegen._constants import FlextInfraCodegenConstants
from flext_infra.codegen._models import FlextInfraCodegenModels
from flext_infra.codegen._utilities import FlextInfraUtilitiesCodegen
from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.codegen.cli import FlextInfraCliCodegen
from flext_infra.codegen.constants_quality_gate import (
    FlextInfraCodegenConstantsQualityGate,
)
from flext_infra.codegen.fixer import FlextInfraCodegenFixer
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from flext_infra.constants import FlextInfraConstants, FlextInfraConstants as c
from flext_infra.deps._constants import FlextInfraDepsConstants
from flext_infra.deps._detector_runtime import FlextInfraDependencyDetectorRuntime
from flext_infra.deps._extra_paths_resolution import (
    FlextInfraExtraPathsResolutionMixin,
)
from flext_infra.deps._internal_sync_repo import FlextInfraInternalSyncRepoMixin
from flext_infra.deps._models import FlextInfraDepsModels
from flext_infra.deps._models_tool_config import FlextInfraDepsModelsToolConfig
from flext_infra.deps._models_tool_config_linters import (
    MypyConfig,
    MypyOverrideConfig,
    PydanticMypyConfig,
    RuffConfig,
    RuffFormatConfig,
    RuffIsortConfig,
    RuffLintConfig,
)
from flext_infra.deps._models_tool_config_type_checkers import (
    PyreflyConfig,
    PyrightConfig,
)
from flext_infra.deps._phases.consolidate_groups import (
    FlextInfraConsolidateGroupsPhase,
)
from flext_infra.deps._phases.ensure_coverage import (
    FlextInfraEnsureCoverageConfigPhase,
)
from flext_infra.deps._phases.ensure_extra_paths import (
    FlextInfraEnsureExtraPathsPhase,
)
from flext_infra.deps._phases.ensure_formatting import (
    FlextInfraEnsureFormattingToolingPhase,
)
from flext_infra.deps._phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
from flext_infra.deps._phases.ensure_namespace import (
    FlextInfraEnsureNamespaceToolingPhase,
)
from flext_infra.deps._phases.ensure_pydantic_mypy import (
    FlextInfraEnsurePydanticMypyConfigPhase,
)
from flext_infra.deps._phases.ensure_pyrefly import (
    FlextInfraEnsurePyreflyConfigPhase,
)
from flext_infra.deps._phases.ensure_pyright import (
    FlextInfraEnsurePyrightConfigPhase,
)
from flext_infra.deps._phases.ensure_pyright_envs import FlextInfraEnsurePyrightEnvs
from flext_infra.deps._phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from flext_infra.deps._phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
from flext_infra.deps._phases.inject_comments import FlextInfraInjectCommentsPhase
from flext_infra.deps.cli import FlextInfraCliDeps
from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from flext_infra.deps.detection_analysis import (
    FlextInfraDependencyDetectionAnalysis,
)
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.extra_paths_pyrefly import FlextInfraExtraPathsPyrefly
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.deps.path_sync import FlextInfraDependencyPathSync
from flext_infra.deps.path_sync_rewrite import FlextInfraDependencyPathSyncRewrite
from flext_infra.detectors._base_detector import (
    DetectorContext,
    FlextInfraScanFileMixin,
)
from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
)
from flext_infra.detectors.compatibility_alias_detector import (
    FlextInfraCompatibilityAliasDetector,
)
from flext_infra.detectors.cyclic_import_detector import (
    FlextInfraCyclicImportDetector,
)
from flext_infra.detectors.dependency_analyzer_base import (
    FlextInfraDependencyAnalyzer,
)
from flext_infra.detectors.future_annotations_detector import (
    FlextInfraFutureAnnotationsDetector,
)
from flext_infra.detectors.import_alias_detector import (
    FlextInfraImportAliasDetector,
)
from flext_infra.detectors.internal_import_detector import (
    FlextInfraInternalImportDetector,
)
from flext_infra.detectors.loose_object_detector import (
    FlextInfraLooseObjectDetector,
)
from flext_infra.detectors.manual_protocol_detector import (
    FlextInfraManualProtocolDetector,
)
from flext_infra.detectors.manual_typing_alias_detector import (
    FlextInfraManualTypingAliasDetector,
)
from flext_infra.detectors.mro_completeness_detector import (
    FlextInfraMROCompletenessDetector,
)
from flext_infra.detectors.namespace_facade_scanner import (
    FlextInfraNamespaceFacadeScanner,
)
from flext_infra.detectors.namespace_source_detector import (
    FlextInfraNamespaceSourceDetector,
)
from flext_infra.detectors.runtime_alias_detector import (
    FlextInfraRuntimeAliasDetector,
)
from flext_infra.docs._auditor_helpers import (
    find_architecture_config,
    parse_audit_gate,
    resolve_checks,
    write_audit_reports,
)
from flext_infra.docs._constants import FlextInfraDocsConstants
from flext_infra.docs._models import FlextInfraDocsModels
from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_infra.docs.cli import FlextInfraCliDocs, FlextInfraDocsCli
from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_infra.gates._base_gate import FlextInfraGate
from flext_infra.gates._gate_registry import FlextInfraGateRegistry
from flext_infra.gates._models import FlextInfraGatesModels
from flext_infra.gates.bandit import FlextInfraBanditGate
from flext_infra.gates.go import FlextInfraGoGate
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_infra.gates.pyright import FlextInfraPyrightGate
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
from flext_infra.github._constants import FlextInfraGithubConstants
from flext_infra.github._models import FlextInfraGithubModels
from flext_infra.github.cli import FlextInfraCliGithub
from flext_infra.models import FlextInfraModels, FlextInfraModels as m
from flext_infra.protocols import FlextInfraProtocols, FlextInfraProtocols as p
from flext_infra.refactor._base_rule import (
    CONTAINER_DICT_SEQ_ADAPTER,
    INFRA_MAPPING_ADAPTER,
    INFRA_SEQ_ADAPTER,
    STR_MAPPING_ADAPTER,
    FlextInfraChangeTracker,
    FlextInfraGenericTransformerRule,
    FlextInfraRefactorRule,
)
from flext_infra.refactor._constants import FlextInfraRefactorConstants
from flext_infra.refactor._engine_orchestration import (
    FlextInfraRefactorEngineOrchestrationMixin,
)
from flext_infra.refactor._engine_pipeline import (
    FlextInfraRefactorEnginePipelineMixin,
)
from flext_infra.refactor._engine_rules import (
    FlextInfraRefactorClassReconstructorRule,
    FlextInfraRefactorLegacyRemovalTextRule,
    FlextInfraRefactorMROClassMigrationTextRule,
    FlextInfraRefactorMRORedundancyChecker,
    FlextInfraRefactorPatternCorrectionsTextRule,
    FlextInfraRefactorSignaturePropagationRule,
    FlextInfraRefactorSymbolPropagationRule,
    FlextInfraRefactorTier0ImportFixRule,
    FlextInfraRefactorTypingAnnotationFixRule,
    FlextInfraRefactorTypingUnificationRule,
)
from flext_infra.refactor._models import FlextInfraRefactorModels
from flext_infra.refactor._models_ast_grep import FlextInfraRefactorAstGrepModels
from flext_infra.refactor._models_census import FlextInfraRefactorModelsCensus
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels,
)
from flext_infra.refactor._models_violations import (
    FlextInfraRefactorModelsViolations,
)
from flext_infra.refactor._namespace_enforcer_phases import (
    FlextInfraNamespaceEnforcerPhasesMixin,
)
from flext_infra.refactor._post_check_gate import FlextInfraPostCheckGate
from flext_infra.refactor._utilities import FlextInfraUtilitiesRefactor
from flext_infra.refactor._utilities_census import FlextInfraUtilitiesRefactorCensus
from flext_infra.refactor._utilities_cli import FlextInfraUtilitiesRefactorCli
from flext_infra.refactor._utilities_engine import FlextInfraUtilitiesRefactorEngine
from flext_infra.refactor._utilities_loader import FlextInfraUtilitiesRefactorLoader
from flext_infra.refactor._utilities_mro_scan import (
    FlextInfraUtilitiesRefactorMroScan,
)
from flext_infra.refactor._utilities_mro_transform import (
    FlextInfraUtilitiesRefactorMroTransform,
)
from flext_infra.refactor._utilities_namespace import (
    FlextInfraUtilitiesRefactorNamespace,
)
from flext_infra.refactor._utilities_namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra.refactor._utilities_namespace_facades import (
    FlextInfraUtilitiesRefactorNamespaceFacades,
)
from flext_infra.refactor._utilities_namespace_moves import (
    FlextInfraUtilitiesRefactorNamespaceMoves,
)
from flext_infra.refactor._utilities_namespace_mro import (
    FlextInfraUtilitiesRefactorNamespaceMro,
)
from flext_infra.refactor._utilities_namespace_runtime import (
    FlextInfraUtilitiesRefactorNamespaceRuntime,
)
from flext_infra.refactor._utilities_policy import FlextInfraUtilitiesRefactorPolicy
from flext_infra.refactor._utilities_pydantic import (
    FlextInfraUtilitiesRefactorPydantic,
)
from flext_infra.refactor._utilities_pydantic_analysis import (
    FlextInfraUtilitiesRefactorPydanticAnalysis,
)
from flext_infra.refactor.census import FlextInfraRefactorCensus
from flext_infra.refactor.class_nesting_analyzer import (
    FlextInfraRefactorClassNestingAnalyzer,
)
from flext_infra.refactor.cli import FlextInfraCliRefactor
from flext_infra.refactor.engine import FlextInfraRefactorEngine
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)
from flext_infra.refactor.mro_import_rewriter import (
    FlextInfraRefactorMROImportRewriter,
)
from flext_infra.refactor.mro_migration_validator import (
    FlextInfraRefactorMROMigrationValidator,
)
from flext_infra.refactor.mro_resolver import FlextInfraRefactorMROResolver
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
from flext_infra.refactor.rule import FlextInfraRefactorRuleLoader
from flext_infra.refactor.rule_definition_validator import (
    FlextInfraRefactorRuleDefinitionValidator,
)
from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
from flext_infra.refactor.violation_analyzer import (
    FlextInfraRefactorViolationAnalyzer,
)
from flext_infra.release._constants import FlextInfraReleaseConstants
from flext_infra.release._models import FlextInfraReleaseModels
from flext_infra.release.cli import FlextInfraCliRelease
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.release.orchestrator_phases import (
    FlextInfraReleaseOrchestratorPhases,
)
from flext_infra.rules.class_nesting import FlextInfraClassNestingRefactorRule
from flext_infra.rules.ensure_future_annotations import (
    FlextInfraRefactorEnsureFutureAnnotationsRule,
)
from flext_infra.rules.import_modernizer import (
    FlextInfraRefactorImportModernizerRule,
)
from flext_infra.rules.legacy_removal import FlextInfraRefactorLegacyRemovalRule
from flext_infra.rules.mro_class_migration import (
    FlextInfraRefactorMROClassMigrationRule,
)
from flext_infra.rules.pattern_corrections import (
    FlextInfraRefactorPatternCorrectionsRule,
)
from flext_infra.transformers._base import (
    FlextInfraChangeTrackingTransformer,
    FlextInfraRopeTransformer,
)
from flext_infra.transformers._utilities_normalizer import (
    FlextInfraNormalizerContext,
    FlextInfraUtilitiesImportNormalizer,
)
from flext_infra.transformers.alias_remover import FlextInfraRefactorAliasRemover
from flext_infra.transformers.census_visitors import (
    FlextInfraCensusImportDiscoveryVisitor,
    FlextInfraCensusUsageCollector,
)
from flext_infra.transformers.class_nesting import (
    FlextInfraRefactorClassNestingTransformer,
)
from flext_infra.transformers.class_reconstructor import (
    FlextInfraRefactorClassReconstructor,
)
from flext_infra.transformers.deprecated_remover import (
    FlextInfraRefactorDeprecatedRemover,
)
from flext_infra.transformers.dict_to_mapping import (
    FlextInfraDictToMappingTransformer,
)
from flext_infra.transformers.helper_consolidation import (
    FlextInfraHelperConsolidationTransformer,
)
from flext_infra.transformers.import_bypass_remover import (
    FlextInfraRefactorImportBypassRemover,
)
from flext_infra.transformers.import_modernizer import (
    FlextInfraRefactorImportModernizer,
)
from flext_infra.transformers.lazy_import_fixer import (
    FlextInfraRefactorLazyImportFixer,
)
from flext_infra.transformers.mro_private_inline import (
    FlextInfraRefactorMROPrivateInlineTransformer,
    FlextInfraRefactorMROQualifiedReferenceTransformer,
)
from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
from flext_infra.transformers.mro_symbol_propagator import (
    FlextInfraRefactorMROSymbolPropagator,
)
from flext_infra.transformers.nested_class_propagation import (
    FlextInfraNestedClassPropagationTransformer,
)
from flext_infra.transformers.policy import (
    FlextInfraRefactorTransformerPolicyUtilities,
)
from flext_infra.transformers.redundant_cast_remover import (
    FlextInfraRedundantCastRemover,
)
from flext_infra.transformers.signature_propagator import (
    FlextInfraRefactorSignaturePropagator,
)
from flext_infra.transformers.symbol_propagator import (
    FlextInfraRefactorSymbolPropagator,
)
from flext_infra.transformers.tier0_import_fixer import (
    FlextInfraTransformerTier0ImportFixer,
)
from flext_infra.transformers.typing_annotation_replacer import (
    FlextInfraTypingAnnotationReplacer,
)
from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
from flext_infra.transformers.violation_census_visitor import (
    FlextInfraViolationCensusVisitor,
)
from flext_infra.typings import FlextInfraTypes, FlextInfraTypes as t
from flext_infra.utilities import FlextInfraUtilities, FlextInfraUtilities as u
from flext_infra.validate._constants import (
    FlextInfraCoreConstants,
    FlextInfraSharedInfraConstants,
)
from flext_infra.validate._models import FlextInfraCoreModels
from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
from flext_infra.validate.cli import FlextInfraCliValidate
from flext_infra.validate.inventory import FlextInfraInventoryService
from flext_infra.validate.namespace_rules import FlextInfraNamespaceRules
from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
from flext_infra.validate.scanner import FlextInfraTextPatternScanner
from flext_infra.validate.skill_validator import FlextInfraSkillValidator
from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
from flext_infra.workspace._constants import FlextInfraWorkspaceConstants
from flext_infra.workspace._models import FlextInfraWorkspaceModels
from flext_infra.workspace.cli import FlextInfraCliWorkspace
from flext_infra.workspace.detector import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceMode,
)
from flext_infra.workspace.maintenance.cli import FlextInfraCliMaintenance
from flext_infra.workspace.maintenance.python_version import (
    FlextInfraPythonVersionEnforcer,
    logger,
)
from flext_infra.workspace.migrator import FlextInfraProjectMigrator
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
from flext_infra.workspace.sync import FlextInfraSyncService
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)

if _t.TYPE_CHECKING:
    import flext_infra._constants as _flext_infra__constants

    _constants = _flext_infra__constants
    import flext_infra._constants.base as _flext_infra__constants_base

    base = _flext_infra__constants_base
    import flext_infra._constants.census as _flext_infra__constants_census

    census = _flext_infra__constants_census
    import flext_infra._constants.make as _flext_infra__constants_make

    make = _flext_infra__constants_make
    import flext_infra._constants.rope as _flext_infra__constants_rope

    rope = _flext_infra__constants_rope
    import flext_infra._constants.source_code as _flext_infra__constants_source_code

    source_code = _flext_infra__constants_source_code
    import flext_infra._models as _flext_infra__models

    _models = _flext_infra__models
    import flext_infra._models.cli_inputs as _flext_infra__models_cli_inputs

    cli_inputs = _flext_infra__models_cli_inputs
    import flext_infra._models.cli_inputs_codegen as _flext_infra__models_cli_inputs_codegen

    cli_inputs_codegen = _flext_infra__models_cli_inputs_codegen
    import flext_infra._models.cli_inputs_ops as _flext_infra__models_cli_inputs_ops

    cli_inputs_ops = _flext_infra__models_cli_inputs_ops
    import flext_infra._models.scan as _flext_infra__models_scan

    scan = _flext_infra__models_scan
    import flext_infra._protocols as _flext_infra__protocols

    _protocols = _flext_infra__protocols
    import flext_infra._typings as _flext_infra__typings

    _typings = _flext_infra__typings
    import flext_infra._typings.adapters as _flext_infra__typings_adapters

    adapters = _flext_infra__typings_adapters
    import flext_infra._utilities as _flext_infra__utilities

    _utilities = _flext_infra__utilities
    import flext_infra._utilities.cli_shared as _flext_infra__utilities_cli_shared

    cli_shared = _flext_infra__utilities_cli_shared
    import flext_infra._utilities.cli_subcommand as _flext_infra__utilities_cli_subcommand

    cli_subcommand = _flext_infra__utilities_cli_subcommand
    import flext_infra._utilities.codegen_constant_analysis as _flext_infra__utilities_codegen_constant_analysis

    codegen_constant_analysis = _flext_infra__utilities_codegen_constant_analysis
    import flext_infra._utilities.codegen_constant_detection as _flext_infra__utilities_codegen_constant_detection

    codegen_constant_detection = _flext_infra__utilities_codegen_constant_detection
    import flext_infra._utilities.codegen_constant_transformation as _flext_infra__utilities_codegen_constant_transformation

    codegen_constant_transformation = (
        _flext_infra__utilities_codegen_constant_transformation
    )
    import flext_infra._utilities.codegen_execution as _flext_infra__utilities_codegen_execution

    codegen_execution = _flext_infra__utilities_codegen_execution
    import flext_infra._utilities.codegen_execution_subprocess as _flext_infra__utilities_codegen_execution_subprocess

    codegen_execution_subprocess = _flext_infra__utilities_codegen_execution_subprocess
    import flext_infra._utilities.codegen_governance as _flext_infra__utilities_codegen_governance

    codegen_governance = _flext_infra__utilities_codegen_governance
    import flext_infra._utilities.codegen_import_cycles as _flext_infra__utilities_codegen_import_cycles

    codegen_import_cycles = _flext_infra__utilities_codegen_import_cycles
    import flext_infra._utilities.codegen_lazy_aliases as _flext_infra__utilities_codegen_lazy_aliases

    codegen_lazy_aliases = _flext_infra__utilities_codegen_lazy_aliases
    import flext_infra._utilities.codegen_lazy_merging as _flext_infra__utilities_codegen_lazy_merging

    codegen_lazy_merging = _flext_infra__utilities_codegen_lazy_merging
    import flext_infra._utilities.codegen_lazy_scanning as _flext_infra__utilities_codegen_lazy_scanning

    codegen_lazy_scanning = _flext_infra__utilities_codegen_lazy_scanning
    import flext_infra._utilities.discovery as _flext_infra__utilities_discovery

    discovery = _flext_infra__utilities_discovery
    import flext_infra._utilities.discovery_scanning as _flext_infra__utilities_discovery_scanning

    discovery_scanning = _flext_infra__utilities_discovery_scanning
    import flext_infra._utilities.docs as _flext_infra__utilities_docs

    docs = _flext_infra__utilities_docs
    import flext_infra._utilities.formatting as _flext_infra__utilities_formatting

    formatting = _flext_infra__utilities_formatting
    import flext_infra._utilities.git as _flext_infra__utilities_git

    git = _flext_infra__utilities_git
    import flext_infra._utilities.github as _flext_infra__utilities_github

    github = _flext_infra__utilities_github
    import flext_infra._utilities.github_pr as _flext_infra__utilities_github_pr

    github_pr = _flext_infra__utilities_github_pr
    import flext_infra._utilities.io as _flext_infra__utilities_io

    io = _flext_infra__utilities_io
    import flext_infra._utilities.iteration as _flext_infra__utilities_iteration

    iteration = _flext_infra__utilities_iteration
    import flext_infra._utilities.log_parser as _flext_infra__utilities_log_parser

    log_parser = _flext_infra__utilities_log_parser
    import flext_infra._utilities.output_reporting as _flext_infra__utilities_output_reporting

    output_reporting = _flext_infra__utilities_output_reporting
    import flext_infra._utilities.parsing as _flext_infra__utilities_parsing

    parsing = _flext_infra__utilities_parsing
    import flext_infra._utilities.paths as _flext_infra__utilities_paths

    paths = _flext_infra__utilities_paths
    import flext_infra._utilities.patterns as _flext_infra__utilities_patterns

    patterns = _flext_infra__utilities_patterns
    import flext_infra._utilities.release as _flext_infra__utilities_release

    release = _flext_infra__utilities_release
    import flext_infra._utilities.reporting as _flext_infra__utilities_reporting

    reporting = _flext_infra__utilities_reporting
    import flext_infra._utilities.rope_analysis as _flext_infra__utilities_rope_analysis

    rope_analysis = _flext_infra__utilities_rope_analysis
    import flext_infra._utilities.rope_analysis_introspection as _flext_infra__utilities_rope_analysis_introspection

    rope_analysis_introspection = _flext_infra__utilities_rope_analysis_introspection
    import flext_infra._utilities.rope_core as _flext_infra__utilities_rope_core

    rope_core = _flext_infra__utilities_rope_core
    import flext_infra._utilities.rope_helpers as _flext_infra__utilities_rope_helpers

    rope_helpers = _flext_infra__utilities_rope_helpers
    import flext_infra._utilities.rope_imports as _flext_infra__utilities_rope_imports

    rope_imports = _flext_infra__utilities_rope_imports
    import flext_infra._utilities.rope_source as _flext_infra__utilities_rope_source

    rope_source = _flext_infra__utilities_rope_source
    import flext_infra._utilities.rule_helpers as _flext_infra__utilities_rule_helpers

    rule_helpers = _flext_infra__utilities_rule_helpers
    import flext_infra._utilities.safety as _flext_infra__utilities_safety

    safety = _flext_infra__utilities_safety
    import flext_infra._utilities.selection as _flext_infra__utilities_selection

    selection = _flext_infra__utilities_selection
    import flext_infra._utilities.subprocess as _flext_infra__utilities_subprocess

    subprocess = _flext_infra__utilities_subprocess
    import flext_infra._utilities.templates as _flext_infra__utilities_templates

    templates = _flext_infra__utilities_templates
    import flext_infra._utilities.terminal as _flext_infra__utilities_terminal

    terminal = _flext_infra__utilities_terminal
    import flext_infra._utilities.toml as _flext_infra__utilities_toml

    toml = _flext_infra__utilities_toml
    import flext_infra._utilities.toml_parse as _flext_infra__utilities_toml_parse

    toml_parse = _flext_infra__utilities_toml_parse
    import flext_infra._utilities.versioning as _flext_infra__utilities_versioning

    versioning = _flext_infra__utilities_versioning
    import flext_infra._utilities.yaml as _flext_infra__utilities_yaml

    yaml = _flext_infra__utilities_yaml
    import flext_infra.basemk as _flext_infra_basemk

    basemk = _flext_infra_basemk
    import flext_infra.basemk.engine as _flext_infra_basemk_engine

    engine = _flext_infra_basemk_engine
    import flext_infra.basemk.generator as _flext_infra_basemk_generator

    generator = _flext_infra_basemk_generator
    import flext_infra.check as _flext_infra_check

    check = _flext_infra_check
    import flext_infra.check.services as _flext_infra_check_services

    services = _flext_infra_check_services
    import flext_infra.check.workspace_check as _flext_infra_check_workspace_check

    workspace_check = _flext_infra_check_workspace_check
    import flext_infra.check.workspace_check_cli as _flext_infra_check_workspace_check_cli

    workspace_check_cli = _flext_infra_check_workspace_check_cli
    import flext_infra.cli as _flext_infra_cli

    cli = _flext_infra_cli
    import flext_infra.codegen as _flext_infra_codegen

    codegen = _flext_infra_codegen
    import flext_infra.codegen.constants_quality_gate as _flext_infra_codegen_constants_quality_gate

    constants_quality_gate = _flext_infra_codegen_constants_quality_gate
    import flext_infra.codegen.fixer as _flext_infra_codegen_fixer

    fixer = _flext_infra_codegen_fixer
    import flext_infra.codegen.lazy_init as _flext_infra_codegen_lazy_init

    lazy_init = _flext_infra_codegen_lazy_init
    import flext_infra.codegen.py_typed as _flext_infra_codegen_py_typed

    py_typed = _flext_infra_codegen_py_typed
    import flext_infra.codegen.scaffolder as _flext_infra_codegen_scaffolder

    scaffolder = _flext_infra_codegen_scaffolder
    import flext_infra.constants as _flext_infra_constants

    constants = _flext_infra_constants
    import flext_infra.deps as _flext_infra_deps

    deps = _flext_infra_deps
    import flext_infra.deps._phases.consolidate_groups as _flext_infra_deps__phases_consolidate_groups

    consolidate_groups = _flext_infra_deps__phases_consolidate_groups
    import flext_infra.deps._phases.ensure_coverage as _flext_infra_deps__phases_ensure_coverage

    ensure_coverage = _flext_infra_deps__phases_ensure_coverage
    import flext_infra.deps._phases.ensure_extra_paths as _flext_infra_deps__phases_ensure_extra_paths

    ensure_extra_paths = _flext_infra_deps__phases_ensure_extra_paths
    import flext_infra.deps._phases.ensure_formatting as _flext_infra_deps__phases_ensure_formatting

    ensure_formatting = _flext_infra_deps__phases_ensure_formatting
    import flext_infra.deps._phases.ensure_mypy as _flext_infra_deps__phases_ensure_mypy

    ensure_mypy = _flext_infra_deps__phases_ensure_mypy
    import flext_infra.deps._phases.ensure_namespace as _flext_infra_deps__phases_ensure_namespace

    ensure_namespace = _flext_infra_deps__phases_ensure_namespace
    import flext_infra.deps._phases.ensure_pydantic_mypy as _flext_infra_deps__phases_ensure_pydantic_mypy

    ensure_pydantic_mypy = _flext_infra_deps__phases_ensure_pydantic_mypy
    import flext_infra.deps._phases.ensure_pyrefly as _flext_infra_deps__phases_ensure_pyrefly

    ensure_pyrefly = _flext_infra_deps__phases_ensure_pyrefly
    import flext_infra.deps._phases.ensure_pyright as _flext_infra_deps__phases_ensure_pyright

    ensure_pyright = _flext_infra_deps__phases_ensure_pyright
    import flext_infra.deps._phases.ensure_pyright_envs as _flext_infra_deps__phases_ensure_pyright_envs

    ensure_pyright_envs = _flext_infra_deps__phases_ensure_pyright_envs
    import flext_infra.deps._phases.ensure_pytest as _flext_infra_deps__phases_ensure_pytest

    ensure_pytest = _flext_infra_deps__phases_ensure_pytest
    import flext_infra.deps._phases.ensure_ruff as _flext_infra_deps__phases_ensure_ruff

    ensure_ruff = _flext_infra_deps__phases_ensure_ruff
    import flext_infra.deps._phases.inject_comments as _flext_infra_deps__phases_inject_comments

    inject_comments = _flext_infra_deps__phases_inject_comments
    import flext_infra.deps.detection as _flext_infra_deps_detection

    detection = _flext_infra_deps_detection
    import flext_infra.deps.detection_analysis as _flext_infra_deps_detection_analysis

    detection_analysis = _flext_infra_deps_detection_analysis
    import flext_infra.deps.detector as _flext_infra_deps_detector

    detector = _flext_infra_deps_detector
    import flext_infra.deps.extra_paths as _flext_infra_deps_extra_paths

    extra_paths = _flext_infra_deps_extra_paths
    import flext_infra.deps.extra_paths_pyrefly as _flext_infra_deps_extra_paths_pyrefly

    extra_paths_pyrefly = _flext_infra_deps_extra_paths_pyrefly
    import flext_infra.deps.fix_pyrefly_config as _flext_infra_deps_fix_pyrefly_config

    fix_pyrefly_config = _flext_infra_deps_fix_pyrefly_config
    import flext_infra.deps.internal_sync as _flext_infra_deps_internal_sync

    internal_sync = _flext_infra_deps_internal_sync
    import flext_infra.deps.modernizer as _flext_infra_deps_modernizer

    modernizer = _flext_infra_deps_modernizer
    import flext_infra.deps.path_sync as _flext_infra_deps_path_sync

    path_sync = _flext_infra_deps_path_sync
    import flext_infra.deps.path_sync_rewrite as _flext_infra_deps_path_sync_rewrite

    path_sync_rewrite = _flext_infra_deps_path_sync_rewrite
    import flext_infra.detectors as _flext_infra_detectors

    detectors = _flext_infra_detectors
    import flext_infra.detectors.class_placement_detector as _flext_infra_detectors_class_placement_detector

    class_placement_detector = _flext_infra_detectors_class_placement_detector
    import flext_infra.detectors.compatibility_alias_detector as _flext_infra_detectors_compatibility_alias_detector

    compatibility_alias_detector = _flext_infra_detectors_compatibility_alias_detector
    import flext_infra.detectors.cyclic_import_detector as _flext_infra_detectors_cyclic_import_detector

    cyclic_import_detector = _flext_infra_detectors_cyclic_import_detector
    import flext_infra.detectors.dependency_analyzer_base as _flext_infra_detectors_dependency_analyzer_base

    dependency_analyzer_base = _flext_infra_detectors_dependency_analyzer_base
    import flext_infra.detectors.future_annotations_detector as _flext_infra_detectors_future_annotations_detector

    future_annotations_detector = _flext_infra_detectors_future_annotations_detector
    import flext_infra.detectors.import_alias_detector as _flext_infra_detectors_import_alias_detector

    import_alias_detector = _flext_infra_detectors_import_alias_detector
    import flext_infra.detectors.internal_import_detector as _flext_infra_detectors_internal_import_detector

    internal_import_detector = _flext_infra_detectors_internal_import_detector
    import flext_infra.detectors.loose_object_detector as _flext_infra_detectors_loose_object_detector

    loose_object_detector = _flext_infra_detectors_loose_object_detector
    import flext_infra.detectors.manual_protocol_detector as _flext_infra_detectors_manual_protocol_detector

    manual_protocol_detector = _flext_infra_detectors_manual_protocol_detector
    import flext_infra.detectors.manual_typing_alias_detector as _flext_infra_detectors_manual_typing_alias_detector

    manual_typing_alias_detector = _flext_infra_detectors_manual_typing_alias_detector
    import flext_infra.detectors.mro_completeness_detector as _flext_infra_detectors_mro_completeness_detector

    mro_completeness_detector = _flext_infra_detectors_mro_completeness_detector
    import flext_infra.detectors.namespace_facade_scanner as _flext_infra_detectors_namespace_facade_scanner

    namespace_facade_scanner = _flext_infra_detectors_namespace_facade_scanner
    import flext_infra.detectors.namespace_source_detector as _flext_infra_detectors_namespace_source_detector

    namespace_source_detector = _flext_infra_detectors_namespace_source_detector
    import flext_infra.detectors.runtime_alias_detector as _flext_infra_detectors_runtime_alias_detector

    runtime_alias_detector = _flext_infra_detectors_runtime_alias_detector
    import flext_infra.docs.auditor as _flext_infra_docs_auditor

    auditor = _flext_infra_docs_auditor
    import flext_infra.docs.builder as _flext_infra_docs_builder

    builder = _flext_infra_docs_builder
    import flext_infra.docs.validator as _flext_infra_docs_validator

    validator = _flext_infra_docs_validator
    import flext_infra.gates as _flext_infra_gates

    gates = _flext_infra_gates
    import flext_infra.gates.bandit as _flext_infra_gates_bandit

    bandit = _flext_infra_gates_bandit
    import flext_infra.gates.go as _flext_infra_gates_go

    go = _flext_infra_gates_go
    import flext_infra.gates.markdown as _flext_infra_gates_markdown

    markdown = _flext_infra_gates_markdown
    import flext_infra.gates.mypy as _flext_infra_gates_mypy

    mypy = _flext_infra_gates_mypy
    import flext_infra.gates.pyrefly as _flext_infra_gates_pyrefly

    pyrefly = _flext_infra_gates_pyrefly
    import flext_infra.gates.pyright as _flext_infra_gates_pyright

    pyright = _flext_infra_gates_pyright
    import flext_infra.gates.ruff_format as _flext_infra_gates_ruff_format

    ruff_format = _flext_infra_gates_ruff_format
    import flext_infra.gates.ruff_lint as _flext_infra_gates_ruff_lint

    ruff_lint = _flext_infra_gates_ruff_lint
    import flext_infra.models as _flext_infra_models

    models = _flext_infra_models
    import flext_infra.protocols as _flext_infra_protocols

    protocols = _flext_infra_protocols
    import flext_infra.refactor as _flext_infra_refactor

    refactor = _flext_infra_refactor
    import flext_infra.refactor.class_nesting_analyzer as _flext_infra_refactor_class_nesting_analyzer

    class_nesting_analyzer = _flext_infra_refactor_class_nesting_analyzer
    import flext_infra.refactor.migrate_to_class_mro as _flext_infra_refactor_migrate_to_class_mro

    migrate_to_class_mro = _flext_infra_refactor_migrate_to_class_mro
    import flext_infra.refactor.mro_import_rewriter as _flext_infra_refactor_mro_import_rewriter

    mro_import_rewriter = _flext_infra_refactor_mro_import_rewriter
    import flext_infra.refactor.mro_migration_validator as _flext_infra_refactor_mro_migration_validator

    mro_migration_validator = _flext_infra_refactor_mro_migration_validator
    import flext_infra.refactor.mro_resolver as _flext_infra_refactor_mro_resolver

    mro_resolver = _flext_infra_refactor_mro_resolver
    import flext_infra.refactor.namespace_enforcer as _flext_infra_refactor_namespace_enforcer

    namespace_enforcer = _flext_infra_refactor_namespace_enforcer
    import flext_infra.refactor.project_classifier as _flext_infra_refactor_project_classifier

    project_classifier = _flext_infra_refactor_project_classifier
    import flext_infra.refactor.rule as _flext_infra_refactor_rule

    rule = _flext_infra_refactor_rule
    import flext_infra.refactor.rule_definition_validator as _flext_infra_refactor_rule_definition_validator

    rule_definition_validator = _flext_infra_refactor_rule_definition_validator
    import flext_infra.refactor.scanner as _flext_infra_refactor_scanner

    scanner = _flext_infra_refactor_scanner
    import flext_infra.refactor.violation_analyzer as _flext_infra_refactor_violation_analyzer

    violation_analyzer = _flext_infra_refactor_violation_analyzer
    import flext_infra.release.orchestrator as _flext_infra_release_orchestrator

    orchestrator = _flext_infra_release_orchestrator
    import flext_infra.release.orchestrator_phases as _flext_infra_release_orchestrator_phases

    orchestrator_phases = _flext_infra_release_orchestrator_phases
    import flext_infra.rules as _flext_infra_rules

    rules = _flext_infra_rules
    import flext_infra.rules.class_nesting as _flext_infra_rules_class_nesting

    class_nesting = _flext_infra_rules_class_nesting
    import flext_infra.rules.ensure_future_annotations as _flext_infra_rules_ensure_future_annotations

    ensure_future_annotations = _flext_infra_rules_ensure_future_annotations
    import flext_infra.rules.import_modernizer as _flext_infra_rules_import_modernizer

    import_modernizer = _flext_infra_rules_import_modernizer
    import flext_infra.rules.legacy_removal as _flext_infra_rules_legacy_removal

    legacy_removal = _flext_infra_rules_legacy_removal
    import flext_infra.rules.mro_class_migration as _flext_infra_rules_mro_class_migration

    mro_class_migration = _flext_infra_rules_mro_class_migration
    import flext_infra.rules.pattern_corrections as _flext_infra_rules_pattern_corrections

    pattern_corrections = _flext_infra_rules_pattern_corrections
    import flext_infra.transformers as _flext_infra_transformers

    transformers = _flext_infra_transformers
    import flext_infra.transformers.alias_remover as _flext_infra_transformers_alias_remover

    alias_remover = _flext_infra_transformers_alias_remover
    import flext_infra.transformers.census_visitors as _flext_infra_transformers_census_visitors

    census_visitors = _flext_infra_transformers_census_visitors
    import flext_infra.transformers.class_reconstructor as _flext_infra_transformers_class_reconstructor

    class_reconstructor = _flext_infra_transformers_class_reconstructor
    import flext_infra.transformers.deprecated_remover as _flext_infra_transformers_deprecated_remover

    deprecated_remover = _flext_infra_transformers_deprecated_remover
    import flext_infra.transformers.dict_to_mapping as _flext_infra_transformers_dict_to_mapping

    dict_to_mapping = _flext_infra_transformers_dict_to_mapping
    import flext_infra.transformers.helper_consolidation as _flext_infra_transformers_helper_consolidation

    helper_consolidation = _flext_infra_transformers_helper_consolidation
    import flext_infra.transformers.import_bypass_remover as _flext_infra_transformers_import_bypass_remover

    import_bypass_remover = _flext_infra_transformers_import_bypass_remover
    import flext_infra.transformers.lazy_import_fixer as _flext_infra_transformers_lazy_import_fixer

    lazy_import_fixer = _flext_infra_transformers_lazy_import_fixer
    import flext_infra.transformers.mro_private_inline as _flext_infra_transformers_mro_private_inline

    mro_private_inline = _flext_infra_transformers_mro_private_inline
    import flext_infra.transformers.mro_remover as _flext_infra_transformers_mro_remover

    mro_remover = _flext_infra_transformers_mro_remover
    import flext_infra.transformers.mro_symbol_propagator as _flext_infra_transformers_mro_symbol_propagator

    mro_symbol_propagator = _flext_infra_transformers_mro_symbol_propagator
    import flext_infra.transformers.nested_class_propagation as _flext_infra_transformers_nested_class_propagation

    nested_class_propagation = _flext_infra_transformers_nested_class_propagation
    import flext_infra.transformers.policy as _flext_infra_transformers_policy

    policy = _flext_infra_transformers_policy
    import flext_infra.transformers.redundant_cast_remover as _flext_infra_transformers_redundant_cast_remover

    redundant_cast_remover = _flext_infra_transformers_redundant_cast_remover
    import flext_infra.transformers.signature_propagator as _flext_infra_transformers_signature_propagator

    signature_propagator = _flext_infra_transformers_signature_propagator
    import flext_infra.transformers.symbol_propagator as _flext_infra_transformers_symbol_propagator

    symbol_propagator = _flext_infra_transformers_symbol_propagator
    import flext_infra.transformers.tier0_import_fixer as _flext_infra_transformers_tier0_import_fixer

    tier0_import_fixer = _flext_infra_transformers_tier0_import_fixer
    import flext_infra.transformers.typing_annotation_replacer as _flext_infra_transformers_typing_annotation_replacer

    typing_annotation_replacer = _flext_infra_transformers_typing_annotation_replacer
    import flext_infra.transformers.typing_unifier as _flext_infra_transformers_typing_unifier

    typing_unifier = _flext_infra_transformers_typing_unifier
    import flext_infra.transformers.violation_census_visitor as _flext_infra_transformers_violation_census_visitor

    violation_census_visitor = _flext_infra_transformers_violation_census_visitor
    import flext_infra.typings as _flext_infra_typings

    typings = _flext_infra_typings
    import flext_infra.utilities as _flext_infra_utilities

    utilities = _flext_infra_utilities
    import flext_infra.validate as _flext_infra_validate

    validate = _flext_infra_validate
    import flext_infra.validate.basemk_validator as _flext_infra_validate_basemk_validator

    basemk_validator = _flext_infra_validate_basemk_validator
    import flext_infra.validate.inventory as _flext_infra_validate_inventory

    inventory = _flext_infra_validate_inventory
    import flext_infra.validate.namespace_rules as _flext_infra_validate_namespace_rules

    namespace_rules = _flext_infra_validate_namespace_rules
    import flext_infra.validate.namespace_validator as _flext_infra_validate_namespace_validator

    namespace_validator = _flext_infra_validate_namespace_validator
    import flext_infra.validate.pytest_diag as _flext_infra_validate_pytest_diag

    pytest_diag = _flext_infra_validate_pytest_diag
    import flext_infra.validate.skill_validator as _flext_infra_validate_skill_validator

    skill_validator = _flext_infra_validate_skill_validator
    import flext_infra.validate.stub_chain as _flext_infra_validate_stub_chain

    stub_chain = _flext_infra_validate_stub_chain
    import flext_infra.workspace as _flext_infra_workspace

    workspace = _flext_infra_workspace
    import flext_infra.workspace.maintenance as _flext_infra_workspace_maintenance

    maintenance = _flext_infra_workspace_maintenance
    import flext_infra.workspace.maintenance.python_version as _flext_infra_workspace_maintenance_python_version

    python_version = _flext_infra_workspace_maintenance_python_version
    import flext_infra.workspace.migrator as _flext_infra_workspace_migrator

    migrator = _flext_infra_workspace_migrator
    import flext_infra.workspace.project_makefile as _flext_infra_workspace_project_makefile

    project_makefile = _flext_infra_workspace_project_makefile
    import flext_infra.workspace.sync as _flext_infra_workspace_sync

    sync = _flext_infra_workspace_sync
    import flext_infra.workspace.workspace_makefile as _flext_infra_workspace_workspace_makefile

    workspace_makefile = _flext_infra_workspace_workspace_makefile

    _ = (
        CONTAINER_DICT_SEQ_ADAPTER,
        DetectorContext,
        FlextInfraBanditGate,
        FlextInfraBaseMkGenerator,
        FlextInfraBaseMkTemplateEngine,
        FlextInfraBaseMkValidator,
        FlextInfraBasemkConstants,
        FlextInfraBasemkModels,
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
        FlextInfraChangeTracker,
        FlextInfraChangeTrackingTransformer,
        FlextInfraCheckConstants,
        FlextInfraCheckModels,
        FlextInfraClassNestingRefactorRule,
        FlextInfraClassPlacementDetector,
        FlextInfraCli,
        FlextInfraCliBasemk,
        FlextInfraCliCheck,
        FlextInfraCliCodegen,
        FlextInfraCliDeps,
        FlextInfraCliDocs,
        FlextInfraCliGithub,
        FlextInfraCliMaintenance,
        FlextInfraCliRefactor,
        FlextInfraCliRelease,
        FlextInfraCliValidate,
        FlextInfraCliWorkspace,
        FlextInfraCodegenCensus,
        FlextInfraCodegenConstants,
        FlextInfraCodegenConstantsQualityGate,
        FlextInfraCodegenFixer,
        FlextInfraCodegenGeneration,
        FlextInfraCodegenLazyInit,
        FlextInfraCodegenModels,
        FlextInfraCodegenPyTyped,
        FlextInfraCodegenScaffolder,
        FlextInfraCodegenSnapshot,
        FlextInfraCompatibilityAliasDetector,
        FlextInfraConfigFixer,
        FlextInfraConsolidateGroupsPhase,
        FlextInfraConstants,
        FlextInfraConstantsBase,
        FlextInfraConstantsCensus,
        FlextInfraConstantsMake,
        FlextInfraConstantsRope,
        FlextInfraConstantsSourceCode,
        FlextInfraCoreConstants,
        FlextInfraCoreModels,
        FlextInfraCyclicImportDetector,
        FlextInfraDependencyAnalyzer,
        FlextInfraDependencyDetectionAnalysis,
        FlextInfraDependencyDetectionService,
        FlextInfraDependencyDetectorRuntime,
        FlextInfraDependencyPathSync,
        FlextInfraDependencyPathSyncRewrite,
        FlextInfraDepsConstants,
        FlextInfraDepsModels,
        FlextInfraDepsModelsToolConfig,
        FlextInfraDictToMappingTransformer,
        FlextInfraDocAuditor,
        FlextInfraDocBuilder,
        FlextInfraDocFixer,
        FlextInfraDocGenerator,
        FlextInfraDocValidator,
        FlextInfraDocsCli,
        FlextInfraDocsConstants,
        FlextInfraDocsModels,
        FlextInfraEnsureCoverageConfigPhase,
        FlextInfraEnsureExtraPathsPhase,
        FlextInfraEnsureFormattingToolingPhase,
        FlextInfraEnsureMypyConfigPhase,
        FlextInfraEnsureNamespaceToolingPhase,
        FlextInfraEnsurePydanticMypyConfigPhase,
        FlextInfraEnsurePyreflyConfigPhase,
        FlextInfraEnsurePyrightConfigPhase,
        FlextInfraEnsurePyrightEnvs,
        FlextInfraEnsurePytestConfigPhase,
        FlextInfraEnsureRuffConfigPhase,
        FlextInfraExtraPathsManager,
        FlextInfraExtraPathsPyrefly,
        FlextInfraExtraPathsResolutionMixin,
        FlextInfraFutureAnnotationsDetector,
        FlextInfraGate,
        FlextInfraGateRegistry,
        FlextInfraGatesModels,
        FlextInfraGenericTransformerRule,
        FlextInfraGithubConstants,
        FlextInfraGithubModels,
        FlextInfraGoGate,
        FlextInfraHelperConsolidationTransformer,
        FlextInfraImportAliasDetector,
        FlextInfraInjectCommentsPhase,
        FlextInfraInternalDependencySyncService,
        FlextInfraInternalImportDetector,
        FlextInfraInternalSyncRepoMixin,
        FlextInfraInventoryService,
        FlextInfraLooseObjectDetector,
        FlextInfraMROCompletenessDetector,
        FlextInfraManualProtocolDetector,
        FlextInfraManualTypingAliasDetector,
        FlextInfraMarkdownGate,
        FlextInfraModels,
        FlextInfraModelsBase,
        FlextInfraModelsCensus,
        FlextInfraModelsCliInputs,
        FlextInfraModelsCliInputsCodegen,
        FlextInfraModelsCliInputsOps,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        FlextInfraMypyGate,
        FlextInfraNamespaceEnforcer,
        FlextInfraNamespaceEnforcerModels,
        FlextInfraNamespaceEnforcerPhasesMixin,
        FlextInfraNamespaceFacadeScanner,
        FlextInfraNamespaceRules,
        FlextInfraNamespaceSourceDetector,
        FlextInfraNamespaceValidator,
        FlextInfraNestedClassPropagationTransformer,
        FlextInfraNormalizerContext,
        FlextInfraOrchestratorService,
        FlextInfraPostCheckGate,
        FlextInfraProjectClassifier,
        FlextInfraProjectMakefileUpdater,
        FlextInfraProjectMigrator,
        FlextInfraProtocols,
        FlextInfraProtocolsBase,
        FlextInfraProtocolsRope,
        FlextInfraPyprojectModernizer,
        FlextInfraPyreflyGate,
        FlextInfraPyrightGate,
        FlextInfraPytestDiagExtractor,
        FlextInfraPythonVersionEnforcer,
        FlextInfraRedundantCastRemover,
        FlextInfraRefactorAliasRemover,
        FlextInfraRefactorAstGrepModels,
        FlextInfraRefactorCensus,
        FlextInfraRefactorClassNestingAnalyzer,
        FlextInfraRefactorClassNestingTransformer,
        FlextInfraRefactorClassReconstructor,
        FlextInfraRefactorClassReconstructorRule,
        FlextInfraRefactorConstants,
        FlextInfraRefactorDeprecatedRemover,
        FlextInfraRefactorEngine,
        FlextInfraRefactorEngineOrchestrationMixin,
        FlextInfraRefactorEnginePipelineMixin,
        FlextInfraRefactorEnsureFutureAnnotationsRule,
        FlextInfraRefactorImportBypassRemover,
        FlextInfraRefactorImportModernizer,
        FlextInfraRefactorImportModernizerRule,
        FlextInfraRefactorLazyImportFixer,
        FlextInfraRefactorLegacyRemovalRule,
        FlextInfraRefactorLegacyRemovalTextRule,
        FlextInfraRefactorLooseClassScanner,
        FlextInfraRefactorMROClassMigrationRule,
        FlextInfraRefactorMROClassMigrationTextRule,
        FlextInfraRefactorMROImportRewriter,
        FlextInfraRefactorMROMigrationValidator,
        FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer,
        FlextInfraRefactorMRORedundancyChecker,
        FlextInfraRefactorMRORemover,
        FlextInfraRefactorMROResolver,
        FlextInfraRefactorMROSymbolPropagator,
        FlextInfraRefactorMigrateToClassMRO,
        FlextInfraRefactorModels,
        FlextInfraRefactorModelsCensus,
        FlextInfraRefactorModelsViolations,
        FlextInfraRefactorPatternCorrectionsRule,
        FlextInfraRefactorPatternCorrectionsTextRule,
        FlextInfraRefactorRule,
        FlextInfraRefactorRuleDefinitionValidator,
        FlextInfraRefactorRuleLoader,
        FlextInfraRefactorSafetyManager,
        FlextInfraRefactorSignaturePropagationRule,
        FlextInfraRefactorSignaturePropagator,
        FlextInfraRefactorSymbolPropagationRule,
        FlextInfraRefactorSymbolPropagator,
        FlextInfraRefactorTier0ImportFixRule,
        FlextInfraRefactorTransformerPolicyUtilities,
        FlextInfraRefactorTypingAnnotationFixRule,
        FlextInfraRefactorTypingUnificationRule,
        FlextInfraRefactorTypingUnifier,
        FlextInfraRefactorViolationAnalyzer,
        FlextInfraReleaseConstants,
        FlextInfraReleaseModels,
        FlextInfraReleaseOrchestrator,
        FlextInfraReleaseOrchestratorPhases,
        FlextInfraRopeTransformer,
        FlextInfraRuffFormatGate,
        FlextInfraRuffLintGate,
        FlextInfraRuntimeAliasDetector,
        FlextInfraRuntimeDevDependencyDetector,
        FlextInfraScanFileMixin,
        FlextInfraSharedInfraConstants,
        FlextInfraSkillValidator,
        FlextInfraStubSupplyChain,
        FlextInfraSyncService,
        FlextInfraTextPatternScanner,
        FlextInfraTransformerTier0ImportFixer,
        FlextInfraTypes,
        FlextInfraTypesAdapters,
        FlextInfraTypesBase,
        FlextInfraTypesRope,
        FlextInfraTypingAnnotationReplacer,
        FlextInfraUtilities,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesCli,
        FlextInfraUtilitiesCliShared,
        FlextInfraUtilitiesCliSubcommand,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCodegenConstantAnalysis,
        FlextInfraUtilitiesCodegenConstantDetection,
        FlextInfraUtilitiesCodegenConstantTransformation,
        FlextInfraUtilitiesCodegenExecution,
        FlextInfraUtilitiesCodegenGovernance,
        FlextInfraUtilitiesCodegenImportCycles,
        FlextInfraUtilitiesCodegenLazyAliases,
        FlextInfraUtilitiesCodegenLazyMerging,
        FlextInfraUtilitiesCodegenLazyScanning,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesDiscoveryScanning,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesFormatting,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesGithubPr,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraUtilitiesIo,
        FlextInfraUtilitiesIteration,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesOutput,
        FlextInfraUtilitiesOutputReporting,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPaths,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesRefactorCli,
        FlextInfraUtilitiesRefactorEngine,
        FlextInfraUtilitiesRefactorLoader,
        FlextInfraUtilitiesRefactorMroScan,
        FlextInfraUtilitiesRefactorMroTransform,
        FlextInfraUtilitiesRefactorNamespace,
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceFacades,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesRefactorNamespaceMro,
        FlextInfraUtilitiesRefactorNamespaceRuntime,
        FlextInfraUtilitiesRefactorPolicy,
        FlextInfraUtilitiesRefactorPydantic,
        FlextInfraUtilitiesRefactorPydanticAnalysis,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesReporting,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesRopeAnalysis,
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRopeCore,
        FlextInfraUtilitiesRopeHelpers,
        FlextInfraUtilitiesRopeImports,
        FlextInfraUtilitiesRopeSource,
        FlextInfraUtilitiesRuleHelpers,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesSelection,
        FlextInfraUtilitiesSubprocess,
        FlextInfraUtilitiesTemplates,
        FlextInfraUtilitiesTerminal,
        FlextInfraUtilitiesToml,
        FlextInfraUtilitiesTomlParse,
        FlextInfraUtilitiesVersioning,
        FlextInfraUtilitiesYaml,
        FlextInfraVersion,
        FlextInfraViolationCensusVisitor,
        FlextInfraWorkspaceCheckGatesMixin,
        FlextInfraWorkspaceChecker,
        FlextInfraWorkspaceCheckerCli,
        FlextInfraWorkspaceConstants,
        FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMakefileGenerator,
        FlextInfraWorkspaceMode,
        FlextInfraWorkspaceModels,
        INFRA_MAPPING_ADAPTER,
        INFRA_SEQ_ADAPTER,
        MypyConfig,
        MypyOverrideConfig,
        PydanticMypyConfig,
        PyreflyConfig,
        PyrightConfig,
        RuffConfig,
        RuffFormatConfig,
        RuffIsortConfig,
        RuffLintConfig,
        STR_MAPPING_ADAPTER,
        __author__,
        __author_email__,
        __description__,
        __license__,
        __title__,
        __url__,
        __version__,
        __version_info__,
        _build_lazy_entries,
        _collapse_to_children,
        _constants,
        _emit_type_checking_module,
        _format_import,
        _format_module_alias_import,
        _format_type_checking_module_alias_import,
        _group_imports,
        _has_flext_types,
        _is_local_module,
        _models,
        _protocols,
        _typings,
        _utilities,
        adapters,
        alias_remover,
        auditor,
        bandit,
        base,
        basemk,
        basemk_validator,
        build_parser,
        builder,
        c,
        census,
        census_visitors,
        check,
        class_nesting,
        class_nesting_analyzer,
        class_placement_detector,
        class_reconstructor,
        cli,
        cli_inputs,
        cli_inputs_codegen,
        cli_inputs_ops,
        cli_shared,
        cli_subcommand,
        codegen,
        codegen_constant_analysis,
        codegen_constant_detection,
        codegen_constant_transformation,
        codegen_execution,
        codegen_execution_subprocess,
        codegen_governance,
        codegen_import_cycles,
        codegen_lazy_aliases,
        codegen_lazy_merging,
        codegen_lazy_scanning,
        compatibility_alias_detector,
        consolidate_groups,
        constants,
        constants_quality_gate,
        cyclic_import_detector,
        d,
        dependency_analyzer_base,
        deprecated_remover,
        deps,
        detection,
        detection_analysis,
        detector,
        detectors,
        dict_to_mapping,
        discovery,
        discovery_scanning,
        docs,
        e,
        engine,
        ensure_coverage,
        ensure_extra_paths,
        ensure_formatting,
        ensure_future_annotations,
        ensure_mypy,
        ensure_namespace,
        ensure_pydantic_mypy,
        ensure_pyrefly,
        ensure_pyright,
        ensure_pyright_envs,
        ensure_pytest,
        ensure_ruff,
        extra_paths,
        extra_paths_pyrefly,
        find_architecture_config,
        fix_pyrefly_config,
        fixer,
        formatting,
        future_annotations_detector,
        gates,
        generator,
        git,
        github,
        github_pr,
        go,
        h,
        helper_consolidation,
        import_alias_detector,
        import_bypass_remover,
        import_modernizer,
        inject_comments,
        internal_import_detector,
        internal_sync,
        inventory,
        io,
        iteration,
        lazy_import_fixer,
        lazy_init,
        legacy_removal,
        log_parser,
        logger,
        loose_object_detector,
        m,
        main,
        maintenance,
        make,
        manual_protocol_detector,
        manual_typing_alias_detector,
        markdown,
        migrate_to_class_mro,
        migrator,
        models,
        modernizer,
        mro_class_migration,
        mro_completeness_detector,
        mro_import_rewriter,
        mro_migration_validator,
        mro_private_inline,
        mro_remover,
        mro_resolver,
        mro_symbol_propagator,
        mypy,
        namespace_enforcer,
        namespace_facade_scanner,
        namespace_rules,
        namespace_source_detector,
        namespace_validator,
        nested_class_propagation,
        orchestrator,
        orchestrator_phases,
        output,
        output_reporting,
        p,
        parse_audit_gate,
        parsing,
        path_sync,
        path_sync_rewrite,
        paths,
        pattern_corrections,
        patterns,
        policy,
        project_classifier,
        project_makefile,
        protocols,
        py_typed,
        pyrefly,
        pyright,
        pytest_diag,
        python_version,
        r,
        redundant_cast_remover,
        refactor,
        release,
        reporting,
        resolve_checks,
        rope,
        rope_analysis,
        rope_analysis_introspection,
        rope_core,
        rope_helpers,
        rope_imports,
        rope_source,
        ruff_format,
        ruff_lint,
        rule,
        rule_definition_validator,
        rule_helpers,
        rules,
        run_cli,
        runtime_alias_detector,
        s,
        safety,
        scaffolder,
        scan,
        scanner,
        selection,
        services,
        signature_propagator,
        skill_validator,
        source_code,
        stub_chain,
        subprocess,
        symbol_propagator,
        sync,
        t,
        templates,
        terminal,
        tier0_import_fixer,
        toml,
        toml_parse,
        transformers,
        typing_annotation_replacer,
        typing_unifier,
        typings,
        u,
        utilities,
        validate,
        validator,
        versioning,
        violation_analyzer,
        violation_census_visitor,
        workspace,
        workspace_check,
        workspace_check_cli,
        workspace_makefile,
        write_audit_reports,
        x,
        yaml,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "flext_infra._constants",
        "flext_infra._models",
        "flext_infra._protocols",
        "flext_infra._typings",
        "flext_infra._utilities",
        "flext_infra.basemk",
        "flext_infra.check",
        "flext_infra.codegen",
        "flext_infra.deps",
        "flext_infra.detectors",
        "flext_infra.docs",
        "flext_infra.gates",
        "flext_infra.github",
        "flext_infra.refactor",
        "flext_infra.release",
        "flext_infra.rules",
        "flext_infra.transformers",
        "flext_infra.validate",
        "flext_infra.workspace",
    ),
    {
        "FlextInfraCli": "flext_infra.cli",
        "FlextInfraConstants": "flext_infra.constants",
        "FlextInfraModels": "flext_infra.models",
        "FlextInfraProtocols": "flext_infra.protocols",
        "FlextInfraTypes": "flext_infra.typings",
        "FlextInfraUtilities": "flext_infra.utilities",
        "FlextInfraVersion": "flext_infra.__version__",
        "__author__": "flext_infra.__version__",
        "__author_email__": "flext_infra.__version__",
        "__description__": "flext_infra.__version__",
        "__license__": "flext_infra.__version__",
        "__title__": "flext_infra.__version__",
        "__url__": "flext_infra.__version__",
        "__version__": "flext_infra.__version__",
        "__version_info__": "flext_infra.__version__",
        "_constants": "flext_infra._constants",
        "_models": "flext_infra._models",
        "_protocols": "flext_infra._protocols",
        "_typings": "flext_infra._typings",
        "_utilities": "flext_infra._utilities",
        "basemk": "flext_infra.basemk",
        "c": ("flext_infra.constants", "FlextInfraConstants"),
        "check": "flext_infra.check",
        "cli": "flext_infra.cli",
        "codegen": "flext_infra.codegen",
        "constants": "flext_infra.constants",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "deps": "flext_infra.deps",
        "detectors": "flext_infra.detectors",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "gates": "flext_infra.gates",
        "h": ("flext_core.handlers", "FlextHandlers"),
        "m": ("flext_infra.models", "FlextInfraModels"),
        "main": "flext_infra.cli",
        "models": "flext_infra.models",
        "p": ("flext_infra.protocols", "FlextInfraProtocols"),
        "protocols": "flext_infra.protocols",
        "r": ("flext_core.result", "FlextResult"),
        "refactor": "flext_infra.refactor",
        "rules": "flext_infra.rules",
        "s": ("flext_core.service", "FlextService"),
        "t": ("flext_infra.typings", "FlextInfraTypes"),
        "transformers": "flext_infra.transformers",
        "typings": "flext_infra.typings",
        "u": ("flext_infra.utilities", "FlextInfraUtilities"),
        "utilities": "flext_infra.utilities",
        "validate": "flext_infra.validate",
        "workspace": "flext_infra.workspace",
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)

__all__ = [
    "CONTAINER_DICT_SEQ_ADAPTER",
    "INFRA_MAPPING_ADAPTER",
    "INFRA_SEQ_ADAPTER",
    "STR_MAPPING_ADAPTER",
    "DetectorContext",
    "FlextInfraBanditGate",
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
    "FlextInfraBaseMkValidator",
    "FlextInfraBasemkConstants",
    "FlextInfraBasemkModels",
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraChangeTracker",
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraCheckConstants",
    "FlextInfraCheckModels",
    "FlextInfraClassNestingRefactorRule",
    "FlextInfraClassPlacementDetector",
    "FlextInfraCli",
    "FlextInfraCliBasemk",
    "FlextInfraCliCheck",
    "FlextInfraCliCodegen",
    "FlextInfraCliDeps",
    "FlextInfraCliDocs",
    "FlextInfraCliGithub",
    "FlextInfraCliMaintenance",
    "FlextInfraCliRefactor",
    "FlextInfraCliRelease",
    "FlextInfraCliValidate",
    "FlextInfraCliWorkspace",
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConstants",
    "FlextInfraCodegenConstantsQualityGate",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenModels",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenSnapshot",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraConstants",
    "FlextInfraConstantsBase",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsMake",
    "FlextInfraConstantsRope",
    "FlextInfraConstantsSourceCode",
    "FlextInfraCoreConstants",
    "FlextInfraCoreModels",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDependencyAnalyzer",
    "FlextInfraDependencyDetectionAnalysis",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDependencyPathSync",
    "FlextInfraDependencyPathSyncRewrite",
    "FlextInfraDepsConstants",
    "FlextInfraDepsModels",
    "FlextInfraDepsModelsToolConfig",
    "FlextInfraDictToMappingTransformer",
    "FlextInfraDocAuditor",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
    "FlextInfraDocsCli",
    "FlextInfraDocsConstants",
    "FlextInfraDocsModels",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureExtraPathsPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePyrightEnvs",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraExtraPathsPyrefly",
    "FlextInfraExtraPathsResolutionMixin",
    "FlextInfraFutureAnnotationsDetector",
    "FlextInfraGate",
    "FlextInfraGateRegistry",
    "FlextInfraGatesModels",
    "FlextInfraGenericTransformerRule",
    "FlextInfraGithubConstants",
    "FlextInfraGithubModels",
    "FlextInfraGoGate",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraImportAliasDetector",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraInternalImportDetector",
    "FlextInfraInternalSyncRepoMixin",
    "FlextInfraInventoryService",
    "FlextInfraLooseObjectDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraMarkdownGate",
    "FlextInfraModels",
    "FlextInfraModelsBase",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCliInputs",
    "FlextInfraModelsCliInputsCodegen",
    "FlextInfraModelsCliInputsOps",
    "FlextInfraModelsRope",
    "FlextInfraModelsScan",
    "FlextInfraMypyGate",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerModels",
    "FlextInfraNamespaceEnforcerPhasesMixin",
    "FlextInfraNamespaceFacadeScanner",
    "FlextInfraNamespaceRules",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraNamespaceValidator",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraNormalizerContext",
    "FlextInfraOrchestratorService",
    "FlextInfraPostCheckGate",
    "FlextInfraProjectClassifier",
    "FlextInfraProjectMakefileUpdater",
    "FlextInfraProjectMigrator",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsRope",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraRedundantCastRemover",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorAstGrepModels",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorConstants",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorEngineOrchestrationMixin",
    "FlextInfraRefactorEnginePipelineMixin",
    "FlextInfraRefactorEnsureFutureAnnotationsRule",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorImportModernizerRule",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorLegacyRemovalRule",
    "FlextInfraRefactorLegacyRemovalTextRule",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROClassMigrationRule",
    "FlextInfraRefactorMROClassMigrationTextRule",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMROPrivateInlineTransformer",
    "FlextInfraRefactorMROQualifiedReferenceTransformer",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorModels",
    "FlextInfraRefactorModelsCensus",
    "FlextInfraRefactorModelsViolations",
    "FlextInfraRefactorPatternCorrectionsRule",
    "FlextInfraRefactorPatternCorrectionsTextRule",
    "FlextInfraRefactorRule",
    "FlextInfraRefactorRuleDefinitionValidator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTier0ImportFixRule",
    "FlextInfraRefactorTransformerPolicyUtilities",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraRefactorViolationAnalyzer",
    "FlextInfraReleaseConstants",
    "FlextInfraReleaseModels",
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseOrchestratorPhases",
    "FlextInfraRopeTransformer",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "FlextInfraRuntimeAliasDetector",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraScanFileMixin",
    "FlextInfraSharedInfraConstants",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraSyncService",
    "FlextInfraTextPatternScanner",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypes",
    "FlextInfraTypesAdapters",
    "FlextInfraTypesBase",
    "FlextInfraTypesRope",
    "FlextInfraTypingAnnotationReplacer",
    "FlextInfraUtilities",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCli",
    "FlextInfraUtilitiesCliShared",
    "FlextInfraUtilitiesCliSubcommand",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenConstantAnalysis",
    "FlextInfraUtilitiesCodegenConstantDetection",
    "FlextInfraUtilitiesCodegenConstantTransformation",
    "FlextInfraUtilitiesCodegenExecution",
    "FlextInfraUtilitiesCodegenGovernance",
    "FlextInfraUtilitiesCodegenImportCycles",
    "FlextInfraUtilitiesCodegenLazyAliases",
    "FlextInfraUtilitiesCodegenLazyMerging",
    "FlextInfraUtilitiesCodegenLazyScanning",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDiscoveryScanning",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesGithubPr",
    "FlextInfraUtilitiesImportNormalizer",
    "FlextInfraUtilitiesIo",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesOutputReporting",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorCli",
    "FlextInfraUtilitiesRefactorEngine",
    "FlextInfraUtilitiesRefactorLoader",
    "FlextInfraUtilitiesRefactorMroScan",
    "FlextInfraUtilitiesRefactorMroTransform",
    "FlextInfraUtilitiesRefactorNamespace",
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceFacades",
    "FlextInfraUtilitiesRefactorNamespaceMoves",
    "FlextInfraUtilitiesRefactorNamespaceMro",
    "FlextInfraUtilitiesRefactorNamespaceRuntime",
    "FlextInfraUtilitiesRefactorPolicy",
    "FlextInfraUtilitiesRefactorPydantic",
    "FlextInfraUtilitiesRefactorPydanticAnalysis",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesRope",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesRuleHelpers",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesSelection",
    "FlextInfraUtilitiesSubprocess",
    "FlextInfraUtilitiesTemplates",
    "FlextInfraUtilitiesTerminal",
    "FlextInfraUtilitiesToml",
    "FlextInfraUtilitiesTomlParse",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesYaml",
    "FlextInfraVersion",
    "FlextInfraViolationCensusVisitor",
    "FlextInfraWorkspaceCheckGatesMixin",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceCheckerCli",
    "FlextInfraWorkspaceConstants",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceMakefileGenerator",
    "FlextInfraWorkspaceMode",
    "FlextInfraWorkspaceModels",
    "MypyConfig",
    "MypyOverrideConfig",
    "PydanticMypyConfig",
    "PyreflyConfig",
    "PyrightConfig",
    "RuffConfig",
    "RuffFormatConfig",
    "RuffIsortConfig",
    "RuffLintConfig",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "_build_lazy_entries",
    "_collapse_to_children",
    "_constants",
    "_emit_type_checking_module",
    "_format_import",
    "_format_module_alias_import",
    "_format_type_checking_module_alias_import",
    "_group_imports",
    "_has_flext_types",
    "_is_local_module",
    "_models",
    "_protocols",
    "_typings",
    "_utilities",
    "adapters",
    "alias_remover",
    "auditor",
    "bandit",
    "base",
    "basemk",
    "basemk_validator",
    "build_parser",
    "builder",
    "c",
    "census",
    "census_visitors",
    "check",
    "class_nesting",
    "class_nesting_analyzer",
    "class_placement_detector",
    "class_reconstructor",
    "cli",
    "cli_inputs",
    "cli_inputs_codegen",
    "cli_inputs_ops",
    "cli_shared",
    "cli_subcommand",
    "codegen",
    "codegen_constant_analysis",
    "codegen_constant_detection",
    "codegen_constant_transformation",
    "codegen_execution",
    "codegen_execution_subprocess",
    "codegen_governance",
    "codegen_import_cycles",
    "codegen_lazy_aliases",
    "codegen_lazy_merging",
    "codegen_lazy_scanning",
    "compatibility_alias_detector",
    "consolidate_groups",
    "constants",
    "constants_quality_gate",
    "cyclic_import_detector",
    "d",
    "dependency_analyzer_base",
    "deprecated_remover",
    "deps",
    "detection",
    "detection_analysis",
    "detector",
    "detectors",
    "dict_to_mapping",
    "discovery",
    "discovery_scanning",
    "docs",
    "e",
    "engine",
    "ensure_coverage",
    "ensure_extra_paths",
    "ensure_formatting",
    "ensure_future_annotations",
    "ensure_mypy",
    "ensure_namespace",
    "ensure_pydantic_mypy",
    "ensure_pyrefly",
    "ensure_pyright",
    "ensure_pyright_envs",
    "ensure_pytest",
    "ensure_ruff",
    "extra_paths",
    "extra_paths_pyrefly",
    "find_architecture_config",
    "fix_pyrefly_config",
    "fixer",
    "formatting",
    "future_annotations_detector",
    "gates",
    "generator",
    "git",
    "github",
    "github_pr",
    "go",
    "h",
    "helper_consolidation",
    "import_alias_detector",
    "import_bypass_remover",
    "import_modernizer",
    "inject_comments",
    "internal_import_detector",
    "internal_sync",
    "inventory",
    "io",
    "iteration",
    "lazy_import_fixer",
    "lazy_init",
    "legacy_removal",
    "log_parser",
    "logger",
    "loose_object_detector",
    "m",
    "main",
    "maintenance",
    "make",
    "manual_protocol_detector",
    "manual_typing_alias_detector",
    "markdown",
    "migrate_to_class_mro",
    "migrator",
    "models",
    "modernizer",
    "mro_class_migration",
    "mro_completeness_detector",
    "mro_import_rewriter",
    "mro_migration_validator",
    "mro_private_inline",
    "mro_remover",
    "mro_resolver",
    "mro_symbol_propagator",
    "mypy",
    "namespace_enforcer",
    "namespace_facade_scanner",
    "namespace_rules",
    "namespace_source_detector",
    "namespace_validator",
    "nested_class_propagation",
    "orchestrator",
    "orchestrator_phases",
    "output",
    "output_reporting",
    "p",
    "parse_audit_gate",
    "parsing",
    "path_sync",
    "path_sync_rewrite",
    "paths",
    "pattern_corrections",
    "patterns",
    "policy",
    "project_classifier",
    "project_makefile",
    "protocols",
    "py_typed",
    "pyrefly",
    "pyright",
    "pytest_diag",
    "python_version",
    "r",
    "redundant_cast_remover",
    "refactor",
    "release",
    "reporting",
    "resolve_checks",
    "rope",
    "rope_analysis",
    "rope_analysis_introspection",
    "rope_core",
    "rope_helpers",
    "rope_imports",
    "rope_source",
    "ruff_format",
    "ruff_lint",
    "rule",
    "rule_definition_validator",
    "rule_helpers",
    "rules",
    "run_cli",
    "runtime_alias_detector",
    "s",
    "safety",
    "scaffolder",
    "scan",
    "scanner",
    "selection",
    "services",
    "signature_propagator",
    "skill_validator",
    "source_code",
    "stub_chain",
    "subprocess",
    "symbol_propagator",
    "sync",
    "t",
    "templates",
    "terminal",
    "tier0_import_fixer",
    "toml",
    "toml_parse",
    "transformers",
    "typing_annotation_replacer",
    "typing_unifier",
    "typings",
    "u",
    "utilities",
    "validate",
    "validator",
    "versioning",
    "violation_analyzer",
    "violation_census_visitor",
    "workspace",
    "workspace_check",
    "workspace_check_cli",
    "workspace_makefile",
    "write_audit_reports",
    "x",
    "yaml",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
