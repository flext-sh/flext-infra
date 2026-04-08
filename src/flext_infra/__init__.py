# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports
from flext_infra.__version__ import *

if _t.TYPE_CHECKING:
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.result import FlextResult as r
    from flext_infra._constants.base import FlextInfraConstantsBase
    from flext_infra._constants.basemk import FlextInfraConstantsBasemk
    from flext_infra._constants.census import FlextInfraConstantsCensus
    from flext_infra._constants.check import FlextInfraConstantsCheck
    from flext_infra._constants.codegen import FlextInfraConstantsCodegen
    from flext_infra._constants.deps import FlextInfraConstantsDeps
    from flext_infra._constants.docs import FlextInfraConstantsDocs
    from flext_infra._constants.github import FlextInfraConstantsGithub
    from flext_infra._constants.make import FlextInfraConstantsMake
    from flext_infra._constants.refactor import FlextInfraConstantsRefactor
    from flext_infra._constants.release import FlextInfraConstantsRelease
    from flext_infra._constants.rope import FlextInfraConstantsRope
    from flext_infra._constants.source_code import FlextInfraConstantsSourceCode
    from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
    from flext_infra._constants.workspace import FlextInfraConstantsWorkspace
    from flext_infra._models.base import FlextInfraModelsBase
    from flext_infra._models.basemk import FlextInfraModelsBasemk
    from flext_infra._models.census import FlextInfraModelsCensus
    from flext_infra._models.check import FlextInfraModelsCheck
    from flext_infra._models.codegen import FlextInfraModelsCodegen
    from flext_infra._models.codegen_deduplication import (
        FlextInfraModelsCodegenDeduplication,
    )
    from flext_infra._models.deps import FlextInfraModelsDeps
    from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolConfig
    from flext_infra._models.deps_tool_config_linters import (
        FlextInfraModelsDepsToolConfigLinters,
    )
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraModelsDepsToolConfigTypeCheckers,
    )
    from flext_infra._models.docs import FlextInfraModelsDocs
    from flext_infra._models.engine import FlextInfraModelsEngine
    from flext_infra._models.engine_ops import FlextInfraModelsEngineOperation
    from flext_infra._models.gates import FlextInfraModelsGates
    from flext_infra._models.github import FlextInfraModelsGithub
    from flext_infra._models.mixins import (
        FlextInfraModelsMixins,
        FlextInfraModelsMixins as x,
    )
    from flext_infra._models.refactor import FlextInfraModelsRefactor
    from flext_infra._models.refactor_ast_grep import FlextInfraModelsRefactorGrep
    from flext_infra._models.refactor_census import FlextInfraModelsRefactorCensus
    from flext_infra._models.refactor_namespace_enforcer import (
        FlextInfraModelsNamespaceEnforcer,
    )
    from flext_infra._models.refactor_violations import (
        FlextInfraModelsRefactorViolations,
    )
    from flext_infra._models.release import FlextInfraModelsRelease
    from flext_infra._models.rope import FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan
    from flext_infra._models.validate import FlextInfraModelsCore
    from flext_infra._models.workspace import FlextInfraModelsWorkspace
    from flext_infra._protocols.base import FlextInfraProtocolsBase
    from flext_infra._protocols.check import (
        FlextInfraProtocolsCheck,
        WorkspaceLoopOutcome,
    )
    from flext_infra._protocols.refactor import (
        FlextInfraChangeTracker,
        FlextInfraProtocolsRefactor,
    )
    from flext_infra._protocols.rope import FlextInfraProtocolsRope
    from flext_infra._typings.adapters import FlextInfraTypesAdapters
    from flext_infra._typings.base import FlextInfraTypesBase
    from flext_infra._typings.rope import FlextInfraTypesRope
    from flext_infra._utilities._utilities import FlextInfraUtilitiesRefactor
    from flext_infra._utilities._utilities_cli import FlextInfraUtilitiesRefactorCli
    from flext_infra._utilities._utilities_mro_transform import (
        FlextInfraUtilitiesRefactorMroTransform,
    )
    from flext_infra._utilities._utilities_namespace import (
        FlextInfraUtilitiesRefactorNamespace,
    )
    from flext_infra._utilities._utilities_namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceMro,
    )
    from flext_infra._utilities._utilities_namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades,
    )
    from flext_infra._utilities._utilities_namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities._utilities_namespace_runtime import (
        FlextInfraUtilitiesRefactorNamespaceRuntime,
    )
    from flext_infra._utilities._utilities_policy import (
        FlextInfraUtilitiesRefactorPolicy,
    )
    from flext_infra._utilities._utilities_pydantic import (
        FlextInfraUtilitiesRefactorPydantic,
    )
    from flext_infra._utilities._utilities_pydantic_analysis import (
        FlextInfraUtilitiesRefactorPydanticAnalysis,
    )
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
    from flext_infra._utilities.cli import FlextInfraUtilitiesCli
    from flext_infra._utilities.cli_shared import FlextInfraUtilitiesCliShared
    from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
    from flext_infra._utilities.codegen_constants import (
        FlextInfraUtilitiesCodegenConstantAnalysis,
        FlextInfraUtilitiesCodegenConstantDetection,
        FlextInfraUtilitiesCodegenConstantTransformation,
        FlextInfraUtilitiesCodegenGovernance,
    )
    from flext_infra._utilities.codegen_execution import (
        FlextInfraUtilitiesCodegenExecution,
    )
    from flext_infra._utilities.codegen_generation import (
        FlextInfraUtilitiesCodegenGeneration,
    )
    from flext_infra._utilities.codegen_import_cycles import (
        FlextInfraUtilitiesCodegenImportCycles,
    )
    from flext_infra._utilities.deps_paths import FlextInfraExtraPathsResolutionMixin
    from flext_infra._utilities.deps_repos import FlextInfraInternalSyncRepoMixin
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.discovery_scanning import (
        FlextInfraUtilitiesDiscoveryScanning,
    )
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
    from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
    from flext_infra._utilities.git import FlextInfraUtilitiesGit
    from flext_infra._utilities.github import FlextInfraUtilitiesGithub
    from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.lazy import (
        FlextInfraUtilitiesCodegenLazyAliases,
        FlextInfraUtilitiesCodegenLazyMerging,
        FlextInfraUtilitiesCodegenLazyScanning,
    )
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.mro_scan import FlextInfraUtilitiesRefactorMroScan
    from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
    from flext_infra._utilities.normalizer import (
        FlextInfraNormalizerContext,
        FlextInfraUtilitiesImportNormalizer,
    )
    from flext_infra._utilities.output import FlextInfraUtilitiesOutput
    from flext_infra._utilities.output_failure_summary import (
        FlextInfraUtilitiesOutputFailureSummary,
    )
    from flext_infra._utilities.output_reporting import (
        FlextInfraUtilitiesOutputReporting,
    )
    from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
    from flext_infra._utilities.paths import FlextInfraUtilitiesPaths
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
    from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
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
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
    from flext_infra._utilities.selection import FlextInfraUtilitiesSelection
    from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
    from flext_infra._utilities.toml import FlextInfraUtilitiesToml
    from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse
    from flext_infra._utilities.transformer_policy import (
        FlextInfraUtilitiesRefactorTransformerPolicy,
    )
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml
    from flext_infra.api import FlextInfra, infra
    from flext_infra.base import FlextInfraServiceBase, s
    from flext_infra.basemk.cli import FlextInfraCliBasemk
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
    from flext_infra.check._workspace_check_gates import (
        FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin,
    )
    from flext_infra.check.cli import FlextInfraCliCheck
    from flext_infra.check.services import FlextInfraCheckServices
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker,
        build_parser,
        run_cli,
    )
    from flext_infra.check.workspace_check_cli import FlextInfraWorkspaceCheckerCli
    from flext_infra.cli import FlextInfraCli
    from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.cli import FlextInfraCliCodegen
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraConstantsCodegenQualityGate,
    )
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
    from flext_infra.constants import FlextInfraConstants, FlextInfraConstants as c
    from flext_infra.deps._detector_runtime import FlextInfraDependencyDetectorRuntime
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
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
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
    from flext_infra.docs._auditor_mixin import FlextInfraDocAuditorMixin
    from flext_infra.docs.auditor import FlextInfraDocAuditor
    from flext_infra.docs.builder import FlextInfraDocBuilder
    from flext_infra.docs.cli import FlextInfraCliDocs
    from flext_infra.docs.fixer import FlextInfraDocFixer
    from flext_infra.docs.generator import FlextInfraDocGenerator
    from flext_infra.docs.validator import FlextInfraDocValidator
    from flext_infra.gates._base_gate import FlextInfraGate
    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.go import FlextInfraGoGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
    from flext_infra.github.cli import FlextInfraCliGithub
    from flext_infra.models import FlextInfraModels, FlextInfraModels as m
    from flext_infra.protocols import FlextInfraProtocols, FlextInfraProtocols as p
    from flext_infra.refactor._base_rule import (
        FlextInfraGenericTransformerRule,
        FlextInfraRefactorRule,
    )
    from flext_infra.refactor._engine_helpers import (
        FlextInfraRefactorEngineHelpersMixin,
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
    from flext_infra.refactor._namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin,
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
    from flext_infra.services._cli_base import FlextInfraServiceCliRunnerMixin
    from flext_infra.services.basemk import FlextInfraServiceBasemkMixin
    from flext_infra.services.check import FlextInfraServiceCheckMixin
    from flext_infra.services.codegen import FlextInfraServiceCodegenMixin
    from flext_infra.services.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.services.deduplicator import FlextInfraCodegenDeduplicator
    from flext_infra.services.deps import FlextInfraServiceDepsMixin
    from flext_infra.services.docs import FlextInfraServiceDocsMixin
    from flext_infra.services.github import FlextInfraServiceGithubMixin
    from flext_infra.services.pipeline import FlextInfraCodegenPipeline
    from flext_infra.services.refactor import FlextInfraServiceRefactorMixin
    from flext_infra.services.release import FlextInfraServiceReleaseMixin
    from flext_infra.services.toml_engine import FlextInfraToml
    from flext_infra.services.validate import FlextInfraServiceValidateMixin
    from flext_infra.services.workspace import FlextInfraServiceWorkspaceMixin
    from flext_infra.transformers._base import (
        FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer,
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
    from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
    from flext_infra.transformers.mro_symbol_propagator import (
        FlextInfraRefactorMROSymbolPropagator,
    )
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer,
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
    from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
    from flext_infra.validate.cli import FlextInfraCliValidate
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.namespace_rules import FlextInfraNamespaceRules
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
    from flext_infra.workspace.cli import FlextInfraCliWorkspace
    from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
    from flext_infra.workspace.maintenance.cli import FlextInfraCliMaintenance
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer,
    )
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
    from flext_infra.workspace.sync import FlextInfraSyncService
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator,
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
        ".github",
        ".refactor",
        ".release",
        ".rules",
        ".services",
        ".transformers",
        ".validate",
        ".workspace",
    ),
    {
        "FlextInfra": ".api",
        "FlextInfraCli": ".cli",
        "FlextInfraConstants": ".constants",
        "FlextInfraModels": ".models",
        "FlextInfraProtocols": ".protocols",
        "FlextInfraServiceBase": ".base",
        "FlextInfraTypes": ".typings",
        "FlextInfraUtilities": ".utilities",
        "FlextInfraVersion": ".__version__",
        "__author__": ".__version__",
        "__author_email__": ".__version__",
        "__description__": ".__version__",
        "__license__": ".__version__",
        "__title__": ".__version__",
        "__url__": ".__version__",
        "__version__": ".__version__",
        "__version_info__": ".__version__",
        "c": (".constants", "FlextInfraConstants"),
        "d": ("flext_core.decorators", "FlextDecorators"),
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "h": ("flext_core.handlers", "FlextHandlers"),
        "infra": ".api",
        "m": (".models", "FlextInfraModels"),
        "p": (".protocols", "FlextInfraProtocols"),
        "r": ("flext_core.result", "FlextResult"),
        "s": ".base",
        "t": (".typings", "FlextInfraTypes"),
        "u": (".utilities", "FlextInfraUtilities"),
    },
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
    ),
    module_name=__name__,
)

__all__ = [
    "DetectorContext",
    "FlextInfra",
    "FlextInfraBanditGate",
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
    "FlextInfraBaseMkValidator",
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraChangeTracker",
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraCheckServices",
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
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenDeduplicator",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenPipeline",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraConstants",
    "FlextInfraConstantsBase",
    "FlextInfraConstantsBasemk",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCheck",
    "FlextInfraConstantsCodegen",
    "FlextInfraConstantsCodegenQualityGate",
    "FlextInfraConstantsDeps",
    "FlextInfraConstantsDocs",
    "FlextInfraConstantsGithub",
    "FlextInfraConstantsMake",
    "FlextInfraConstantsRefactor",
    "FlextInfraConstantsRelease",
    "FlextInfraConstantsRope",
    "FlextInfraConstantsSharedInfra",
    "FlextInfraConstantsSourceCode",
    "FlextInfraConstantsWorkspace",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDependencyDetectionAnalysis",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDependencyPathSync",
    "FlextInfraDependencyPathSyncRewrite",
    "FlextInfraDocAuditor",
    "FlextInfraDocAuditorMixin",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
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
    "FlextInfraGenericTransformerRule",
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
    "FlextInfraModelsBasemk",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCheck",
    "FlextInfraModelsCodegen",
    "FlextInfraModelsCodegenDeduplication",
    "FlextInfraModelsCore",
    "FlextInfraModelsDeps",
    "FlextInfraModelsDepsToolConfig",
    "FlextInfraModelsDepsToolConfigLinters",
    "FlextInfraModelsDepsToolConfigTypeCheckers",
    "FlextInfraModelsDocs",
    "FlextInfraModelsEngine",
    "FlextInfraModelsEngineOperation",
    "FlextInfraModelsGates",
    "FlextInfraModelsGithub",
    "FlextInfraModelsMixins",
    "FlextInfraModelsNamespaceEnforcer",
    "FlextInfraModelsRefactor",
    "FlextInfraModelsRefactorCensus",
    "FlextInfraModelsRefactorGrep",
    "FlextInfraModelsRefactorViolations",
    "FlextInfraModelsRelease",
    "FlextInfraModelsRope",
    "FlextInfraModelsScan",
    "FlextInfraModelsWorkspace",
    "FlextInfraMypyGate",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerPhasesMixin",
    "FlextInfraNamespaceFacadeScanner",
    "FlextInfraNamespaceRules",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraNamespaceValidator",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraNormalizerContext",
    "FlextInfraOrchestratorService",
    "FlextInfraProjectClassifier",
    "FlextInfraProjectMakefileUpdater",
    "FlextInfraProjectMigrator",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsCheck",
    "FlextInfraProtocolsRefactor",
    "FlextInfraProtocolsRope",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorEngineHelpersMixin",
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
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorMigrateToClassMRO",
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
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraRefactorViolationAnalyzer",
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseOrchestratorPhases",
    "FlextInfraRopeTransformer",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "FlextInfraRuntimeAliasDetector",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraScanFileMixin",
    "FlextInfraServiceBase",
    "FlextInfraServiceBasemkMixin",
    "FlextInfraServiceCheckMixin",
    "FlextInfraServiceCliRunnerMixin",
    "FlextInfraServiceCodegenMixin",
    "FlextInfraServiceDepsMixin",
    "FlextInfraServiceDocsMixin",
    "FlextInfraServiceGithubMixin",
    "FlextInfraServiceRefactorMixin",
    "FlextInfraServiceReleaseMixin",
    "FlextInfraServiceValidateMixin",
    "FlextInfraServiceWorkspaceMixin",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraSyncService",
    "FlextInfraTextPatternScanner",
    "FlextInfraToml",
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
    "FlextInfraUtilitiesCodegenGeneration",
    "FlextInfraUtilitiesCodegenGovernance",
    "FlextInfraUtilitiesCodegenImportCycles",
    "FlextInfraUtilitiesCodegenLazyAliases",
    "FlextInfraUtilitiesCodegenLazyMerging",
    "FlextInfraUtilitiesCodegenLazyScanning",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDiscoveryScanning",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsValidate",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesGithubPr",
    "FlextInfraUtilitiesImportNormalizer",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesOutputFailureSummary",
    "FlextInfraUtilitiesOutputReporting",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorCli",
    "FlextInfraUtilitiesRefactorEngine",
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
    "FlextInfraUtilitiesRefactorTransformerPolicy",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesRope",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesSelection",
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
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceMakefileGenerator",
    "WorkspaceLoopOutcome",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "build_parser",
    "c",
    "d",
    "e",
    "h",
    "infra",
    "m",
    "p",
    "r",
    "run_cli",
    "s",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
