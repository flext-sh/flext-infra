# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Flext infra package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports
from flext_infra.__version__ import *

if _t.TYPE_CHECKING:
    import flext_infra._constants as _flext_infra__constants

    _constants = _flext_infra__constants
    import flext_infra._models as _flext_infra__models
    from flext_infra._constants import (
        FlextInfraConstantsBase,
        FlextInfraConstantsBasemk,
        FlextInfraConstantsCensus,
        FlextInfraConstantsCheck,
        FlextInfraConstantsCodegen,
        FlextInfraConstantsCore,
        FlextInfraConstantsDeps,
        FlextInfraConstantsDocs,
        FlextInfraConstantsGithub,
        FlextInfraConstantsMake,
        FlextInfraConstantsRefactor,
        FlextInfraConstantsRelease,
        FlextInfraConstantsRope,
        FlextInfraConstantsSharedInfra,
        FlextInfraConstantsSourceCode,
        FlextInfraConstantsWorkspace,
    )

    _models = _flext_infra__models
    import flext_infra._protocols as _flext_infra__protocols
    from flext_infra._models import (
        FlextInfraModelsBase,
        FlextInfraModelsBasemk,
        FlextInfraModelsCensus,
        FlextInfraModelsCheck,
        FlextInfraModelsCodegen,
        FlextInfraModelsCodegenDeduplication,
        FlextInfraModelsCore,
        FlextInfraModelsDeps,
        FlextInfraModelsDepsToolConfig,
        FlextInfraModelsDepsToolConfigLinters,
        FlextInfraModelsDepsToolConfigTypeCheckers,
        FlextInfraModelsDocs,
        FlextInfraModelsEngine,
        FlextInfraModelsEngineOperation,
        FlextInfraModelsGates,
        FlextInfraModelsGithub,
        FlextInfraModelsMixins,
        FlextInfraModelsMixins as x,
        FlextInfraModelsNamespaceEnforcer,
        FlextInfraModelsRefactor,
        FlextInfraModelsRefactorCensus,
        FlextInfraModelsRefactorGrep,
        FlextInfraModelsRefactorViolations,
        FlextInfraModelsRelease,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        FlextInfraModelsWorkspace,
    )

    _protocols = _flext_infra__protocols
    import flext_infra._typings as _flext_infra__typings
    from flext_infra._protocols import (
        FlextInfraChangeTracker,
        FlextInfraProtocolsBase,
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsRefactor,
        FlextInfraProtocolsRope,
        WorkspaceLoopOutcome,
    )

    _typings = _flext_infra__typings
    import flext_infra._utilities as _flext_infra__utilities
    from flext_infra._typings import (
        FlextInfraTypesAdapters,
        FlextInfraTypesBase,
        FlextInfraTypesRope,
    )

    _utilities = _flext_infra__utilities
    import flext_infra.api as _flext_infra_api
    from flext_infra._utilities import (
        FlextInfraExtraPathsResolutionMixin,
        FlextInfraInternalSyncRepoMixin,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesCli,
        FlextInfraUtilitiesCliShared,
        FlextInfraUtilitiesCliSubcommand,
        FlextInfraUtilitiesCodegenConstantAnalysis,
        FlextInfraUtilitiesCodegenConstantDetection,
        FlextInfraUtilitiesCodegenConstantTransformation,
        FlextInfraUtilitiesCodegenExecution,
        FlextInfraUtilitiesCodegenGeneration,
        FlextInfraUtilitiesCodegenGovernance,
        FlextInfraUtilitiesCodegenImportCycles,
        FlextInfraUtilitiesCodegenLazyAliases,
        FlextInfraUtilitiesCodegenLazyMerging,
        FlextInfraUtilitiesCodegenLazyScanning,
        FlextInfraUtilitiesCodegenNamespace,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesDiscoveryScanning,
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
        FlextInfraUtilitiesFormatting,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesGithubPr,
        FlextInfraUtilitiesIteration,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesOutput,
        FlextInfraUtilitiesOutputReporting,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPaths,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesReporting,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesRopeAnalysis,
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRopeCore,
        FlextInfraUtilitiesRopeHelpers,
        FlextInfraUtilitiesRopeImports,
        FlextInfraUtilitiesRopeSource,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesSelection,
        FlextInfraUtilitiesTerminal,
        FlextInfraUtilitiesToml,
        FlextInfraUtilitiesTomlParse,
        FlextInfraUtilitiesVersioning,
        FlextInfraUtilitiesYaml,
    )

    api = _flext_infra_api
    import flext_infra.base as _flext_infra_base
    from flext_infra.api import FlextInfra, infra

    base = _flext_infra_base
    import flext_infra.cli as _flext_infra_cli
    from flext_infra.base import FlextInfraCommandContext, FlextInfraServiceBase, s
    from flext_infra.basemk.cli import FlextInfraCliBasemk
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
    from flext_infra.check._workspace_check_gates import (
        FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin,
    )
    from flext_infra.check.cli import FlextInfraCliCheck
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker,
        build_parser,
        run_cli,
    )
    from flext_infra.check.workspace_check_cli import FlextInfraWorkspaceCheckerCli

    cli = _flext_infra_cli
    import flext_infra.constants as _flext_infra_constants
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
    from flext_infra.cli import FlextInfraCli, main
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

    constants = _flext_infra_constants
    import flext_infra.models as _flext_infra_models
    from flext_infra.constants import FlextInfraConstants, FlextInfraConstants as c
    from flext_infra.deps._detector_runtime import FlextInfraDependencyDetectorRuntime
    from flext_infra.deps._phases import (
        FlextInfraConsolidateGroupsPhase,
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
        FlextInfraInjectCommentsPhase,
    )
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

    models = _flext_infra_models
    import flext_infra.protocols as _flext_infra_protocols
    from flext_infra.models import FlextInfraModels, FlextInfraModels as m

    protocols = _flext_infra_protocols
    import flext_infra.typings as _flext_infra_typings
    from flext_infra._utilities import FlextInfraUtilitiesRefactor
    from flext_infra._utilities._utilities_census import (
        FlextInfraUtilitiesRefactorCensus,
    )
    from flext_infra._utilities._utilities_cli import FlextInfraUtilitiesRefactorCli
    from flext_infra._utilities._utilities_engine import (
        FlextInfraUtilitiesRefactorEngine,
    )
    from flext_infra._utilities._utilities_mro_scan import (
        FlextInfraUtilitiesRefactorMroScan,
    )
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
    from flext_infra._utilities.import_normalizer import (
        FlextInfraNormalizerContext,
        FlextInfraUtilitiesImportNormalizer,
    )
    from flext_infra._utilities.transformer_policy import (
        FlextInfraUtilitiesRefactorTransformerPolicy,
    )
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

    typings = _flext_infra_typings
    import flext_infra.utilities as _flext_infra_utilities
    from flext_infra.typings import FlextInfraTypes, FlextInfraTypes as t

    utilities = _flext_infra_utilities
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.result import FlextResult as r
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
        logger,
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
        "flext_infra._constants",
        "flext_infra._models",
        "flext_infra._protocols",
        "flext_infra._typings",
        "flext_infra._utilities",
    ),
    {
        "DetectorContext": ("flext_infra.detectors._base_detector", "DetectorContext"),
        "FlextInfra": ("flext_infra.api", "FlextInfra"),
        "FlextInfraBanditGate": ("flext_infra.gates.bandit", "FlextInfraBanditGate"),
        "FlextInfraBaseMkGenerator": (
            "flext_infra.basemk.generator",
            "FlextInfraBaseMkGenerator",
        ),
        "FlextInfraBaseMkTemplateEngine": (
            "flext_infra.basemk.engine",
            "FlextInfraBaseMkTemplateEngine",
        ),
        "FlextInfraBaseMkValidator": (
            "flext_infra.validate.basemk_validator",
            "FlextInfraBaseMkValidator",
        ),
        "FlextInfraCensusImportDiscoveryVisitor": (
            "flext_infra.transformers.census_visitors",
            "FlextInfraCensusImportDiscoveryVisitor",
        ),
        "FlextInfraCensusUsageCollector": (
            "flext_infra.transformers.census_visitors",
            "FlextInfraCensusUsageCollector",
        ),
        "FlextInfraChangeTrackingTransformer": (
            "flext_infra.transformers._base",
            "FlextInfraChangeTrackingTransformer",
        ),
        "FlextInfraClassNestingRefactorRule": (
            "flext_infra.rules.class_nesting",
            "FlextInfraClassNestingRefactorRule",
        ),
        "FlextInfraClassPlacementDetector": (
            "flext_infra.detectors.class_placement_detector",
            "FlextInfraClassPlacementDetector",
        ),
        "FlextInfraCli": ("flext_infra.cli", "FlextInfraCli"),
        "FlextInfraCliBasemk": ("flext_infra.basemk.cli", "FlextInfraCliBasemk"),
        "FlextInfraCliCheck": ("flext_infra.check.cli", "FlextInfraCliCheck"),
        "FlextInfraCliCodegen": ("flext_infra.codegen.cli", "FlextInfraCliCodegen"),
        "FlextInfraCliDeps": ("flext_infra.deps.cli", "FlextInfraCliDeps"),
        "FlextInfraCliDocs": ("flext_infra.docs.cli", "FlextInfraCliDocs"),
        "FlextInfraCliGithub": ("flext_infra.github.cli", "FlextInfraCliGithub"),
        "FlextInfraCliMaintenance": (
            "flext_infra.workspace.maintenance.cli",
            "FlextInfraCliMaintenance",
        ),
        "FlextInfraCliRefactor": ("flext_infra.refactor.cli", "FlextInfraCliRefactor"),
        "FlextInfraCliRelease": ("flext_infra.release.cli", "FlextInfraCliRelease"),
        "FlextInfraCliValidate": ("flext_infra.validate.cli", "FlextInfraCliValidate"),
        "FlextInfraCliWorkspace": (
            "flext_infra.workspace.cli",
            "FlextInfraCliWorkspace",
        ),
        "FlextInfraCodegenCensus": (
            "flext_infra.codegen.census",
            "FlextInfraCodegenCensus",
        ),
        "FlextInfraCodegenConsolidator": (
            "flext_infra.services.consolidator",
            "FlextInfraCodegenConsolidator",
        ),
        "FlextInfraConstantsCodegenQualityGate": (
            "flext_infra.codegen.constants_quality_gate",
            "FlextInfraConstantsCodegenQualityGate",
        ),
        "FlextInfraCodegenDeduplicator": (
            "flext_infra.services.deduplicator",
            "FlextInfraCodegenDeduplicator",
        ),
        "FlextInfraCodegenFixer": (
            "flext_infra.codegen.fixer",
            "FlextInfraCodegenFixer",
        ),
        "FlextInfraCodegenGeneration": (
            "flext_infra.codegen._codegen_generation",
            "FlextInfraCodegenGeneration",
        ),
        "FlextInfraCodegenLazyInit": (
            "flext_infra.codegen.lazy_init",
            "FlextInfraCodegenLazyInit",
        ),
        "FlextInfraCodegenPipeline": (
            "flext_infra.services.pipeline",
            "FlextInfraCodegenPipeline",
        ),
        "FlextInfraCodegenPyTyped": (
            "flext_infra.codegen.py_typed",
            "FlextInfraCodegenPyTyped",
        ),
        "FlextInfraCodegenScaffolder": (
            "flext_infra.codegen.scaffolder",
            "FlextInfraCodegenScaffolder",
        ),
        "FlextInfraCommandContext": ("flext_infra.base", "FlextInfraCommandContext"),
        "FlextInfraCompatibilityAliasDetector": (
            "flext_infra.detectors.compatibility_alias_detector",
            "FlextInfraCompatibilityAliasDetector",
        ),
        "FlextInfraConfigFixer": (
            "flext_infra.deps.fix_pyrefly_config",
            "FlextInfraConfigFixer",
        ),
        "FlextInfraConsolidateGroupsPhase": (
            "flext_infra.deps._phases.consolidate_groups",
            "FlextInfraConsolidateGroupsPhase",
        ),
        "FlextInfraConstants": ("flext_infra.constants", "FlextInfraConstants"),
        "FlextInfraCyclicImportDetector": (
            "flext_infra.detectors.cyclic_import_detector",
            "FlextInfraCyclicImportDetector",
        ),
        "FlextInfraDependencyDetectionAnalysis": (
            "flext_infra.deps.detection_analysis",
            "FlextInfraDependencyDetectionAnalysis",
        ),
        "FlextInfraDependencyDetectionService": (
            "flext_infra.deps.detection",
            "FlextInfraDependencyDetectionService",
        ),
        "FlextInfraDependencyDetectorRuntime": (
            "flext_infra.deps._detector_runtime",
            "FlextInfraDependencyDetectorRuntime",
        ),
        "FlextInfraDependencyPathSync": (
            "flext_infra.deps.path_sync",
            "FlextInfraDependencyPathSync",
        ),
        "FlextInfraDependencyPathSyncRewrite": (
            "flext_infra.deps.path_sync_rewrite",
            "FlextInfraDependencyPathSyncRewrite",
        ),
        "FlextInfraDocAuditor": ("flext_infra.docs.auditor", "FlextInfraDocAuditor"),
        "FlextInfraDocAuditorMixin": (
            "flext_infra.docs._auditor_mixin",
            "FlextInfraDocAuditorMixin",
        ),
        "FlextInfraDocBuilder": ("flext_infra.docs.builder", "FlextInfraDocBuilder"),
        "FlextInfraDocFixer": ("flext_infra.docs.fixer", "FlextInfraDocFixer"),
        "FlextInfraDocGenerator": (
            "flext_infra.docs.generator",
            "FlextInfraDocGenerator",
        ),
        "FlextInfraDocValidator": (
            "flext_infra.docs.validator",
            "FlextInfraDocValidator",
        ),
        "FlextInfraEnsureCoverageConfigPhase": (
            "flext_infra.deps._phases.ensure_coverage",
            "FlextInfraEnsureCoverageConfigPhase",
        ),
        "FlextInfraEnsureExtraPathsPhase": (
            "flext_infra.deps._phases.ensure_extra_paths",
            "FlextInfraEnsureExtraPathsPhase",
        ),
        "FlextInfraEnsureFormattingToolingPhase": (
            "flext_infra.deps._phases.ensure_formatting",
            "FlextInfraEnsureFormattingToolingPhase",
        ),
        "FlextInfraEnsureMypyConfigPhase": (
            "flext_infra.deps._phases.ensure_mypy",
            "FlextInfraEnsureMypyConfigPhase",
        ),
        "FlextInfraEnsureNamespaceToolingPhase": (
            "flext_infra.deps._phases.ensure_namespace",
            "FlextInfraEnsureNamespaceToolingPhase",
        ),
        "FlextInfraEnsurePydanticMypyConfigPhase": (
            "flext_infra.deps._phases.ensure_pydantic_mypy",
            "FlextInfraEnsurePydanticMypyConfigPhase",
        ),
        "FlextInfraEnsurePyreflyConfigPhase": (
            "flext_infra.deps._phases.ensure_pyrefly",
            "FlextInfraEnsurePyreflyConfigPhase",
        ),
        "FlextInfraEnsurePyrightConfigPhase": (
            "flext_infra.deps._phases.ensure_pyright",
            "FlextInfraEnsurePyrightConfigPhase",
        ),
        "FlextInfraEnsurePyrightEnvs": (
            "flext_infra.deps._phases.ensure_pyright_envs",
            "FlextInfraEnsurePyrightEnvs",
        ),
        "FlextInfraEnsurePytestConfigPhase": (
            "flext_infra.deps._phases.ensure_pytest",
            "FlextInfraEnsurePytestConfigPhase",
        ),
        "FlextInfraEnsureRuffConfigPhase": (
            "flext_infra.deps._phases.ensure_ruff",
            "FlextInfraEnsureRuffConfigPhase",
        ),
        "FlextInfraExtraPathsManager": (
            "flext_infra.deps.extra_paths",
            "FlextInfraExtraPathsManager",
        ),
        "FlextInfraExtraPathsPyrefly": (
            "flext_infra.deps.extra_paths_pyrefly",
            "FlextInfraExtraPathsPyrefly",
        ),
        "FlextInfraFutureAnnotationsDetector": (
            "flext_infra.detectors.future_annotations_detector",
            "FlextInfraFutureAnnotationsDetector",
        ),
        "FlextInfraGate": ("flext_infra.gates._base_gate", "FlextInfraGate"),
        "FlextInfraGateRegistry": (
            "flext_infra.check._workspace_check_gates",
            "FlextInfraGateRegistry",
        ),
        "FlextInfraGenericTransformerRule": (
            "flext_infra.refactor._base_rule",
            "FlextInfraGenericTransformerRule",
        ),
        "FlextInfraGoGate": ("flext_infra.gates.go", "FlextInfraGoGate"),
        "FlextInfraHelperConsolidationTransformer": (
            "flext_infra.transformers.helper_consolidation",
            "FlextInfraHelperConsolidationTransformer",
        ),
        "FlextInfraImportAliasDetector": (
            "flext_infra.detectors.import_alias_detector",
            "FlextInfraImportAliasDetector",
        ),
        "FlextInfraInjectCommentsPhase": (
            "flext_infra.deps._phases.inject_comments",
            "FlextInfraInjectCommentsPhase",
        ),
        "FlextInfraInternalDependencySyncService": (
            "flext_infra.deps.internal_sync",
            "FlextInfraInternalDependencySyncService",
        ),
        "FlextInfraInternalImportDetector": (
            "flext_infra.detectors.internal_import_detector",
            "FlextInfraInternalImportDetector",
        ),
        "FlextInfraInventoryService": (
            "flext_infra.validate.inventory",
            "FlextInfraInventoryService",
        ),
        "FlextInfraLooseObjectDetector": (
            "flext_infra.detectors.loose_object_detector",
            "FlextInfraLooseObjectDetector",
        ),
        "FlextInfraMROCompletenessDetector": (
            "flext_infra.detectors.mro_completeness_detector",
            "FlextInfraMROCompletenessDetector",
        ),
        "FlextInfraManualProtocolDetector": (
            "flext_infra.detectors.manual_protocol_detector",
            "FlextInfraManualProtocolDetector",
        ),
        "FlextInfraManualTypingAliasDetector": (
            "flext_infra.detectors.manual_typing_alias_detector",
            "FlextInfraManualTypingAliasDetector",
        ),
        "FlextInfraMarkdownGate": (
            "flext_infra.gates.markdown",
            "FlextInfraMarkdownGate",
        ),
        "FlextInfraModels": ("flext_infra.models", "FlextInfraModels"),
        "FlextInfraMypyGate": ("flext_infra.gates.mypy", "FlextInfraMypyGate"),
        "FlextInfraNamespaceEnforcer": (
            "flext_infra.refactor.namespace_enforcer",
            "FlextInfraNamespaceEnforcer",
        ),
        "FlextInfraNamespaceEnforcerPhasesMixin": (
            "flext_infra.refactor._namespace_enforcer_phases",
            "FlextInfraNamespaceEnforcerPhasesMixin",
        ),
        "FlextInfraNamespaceFacadeScanner": (
            "flext_infra.detectors.namespace_facade_scanner",
            "FlextInfraNamespaceFacadeScanner",
        ),
        "FlextInfraNamespaceRules": (
            "flext_infra.validate.namespace_rules",
            "FlextInfraNamespaceRules",
        ),
        "FlextInfraNamespaceSourceDetector": (
            "flext_infra.detectors.namespace_source_detector",
            "FlextInfraNamespaceSourceDetector",
        ),
        "FlextInfraNamespaceValidator": (
            "flext_infra.validate.namespace_validator",
            "FlextInfraNamespaceValidator",
        ),
        "FlextInfraNestedClassPropagationTransformer": (
            "flext_infra.transformers.nested_class_propagation",
            "FlextInfraNestedClassPropagationTransformer",
        ),
        "FlextInfraNormalizerContext": (
            "flext_infra._utilities.import_normalizer",
            "FlextInfraNormalizerContext",
        ),
        "FlextInfraOrchestratorService": (
            "flext_infra.workspace.orchestrator",
            "FlextInfraOrchestratorService",
        ),
        "FlextInfraProjectClassifier": (
            "flext_infra.refactor.project_classifier",
            "FlextInfraProjectClassifier",
        ),
        "FlextInfraProjectMakefileUpdater": (
            "flext_infra.workspace.project_makefile",
            "FlextInfraProjectMakefileUpdater",
        ),
        "FlextInfraProjectMigrator": (
            "flext_infra.workspace.migrator",
            "FlextInfraProjectMigrator",
        ),
        "FlextInfraProtocols": ("flext_infra.protocols", "FlextInfraProtocols"),
        "FlextInfraPyprojectModernizer": (
            "flext_infra.deps.modernizer",
            "FlextInfraPyprojectModernizer",
        ),
        "FlextInfraPyreflyGate": ("flext_infra.gates.pyrefly", "FlextInfraPyreflyGate"),
        "FlextInfraPyrightGate": ("flext_infra.gates.pyright", "FlextInfraPyrightGate"),
        "FlextInfraPytestDiagExtractor": (
            "flext_infra.validate.pytest_diag",
            "FlextInfraPytestDiagExtractor",
        ),
        "FlextInfraPythonVersionEnforcer": (
            "flext_infra.workspace.maintenance.python_version",
            "FlextInfraPythonVersionEnforcer",
        ),
        "FlextInfraRefactorAliasRemover": (
            "flext_infra.transformers.alias_remover",
            "FlextInfraRefactorAliasRemover",
        ),
        "FlextInfraRefactorCensus": (
            "flext_infra.refactor.census",
            "FlextInfraRefactorCensus",
        ),
        "FlextInfraRefactorClassNestingAnalyzer": (
            "flext_infra.refactor.class_nesting_analyzer",
            "FlextInfraRefactorClassNestingAnalyzer",
        ),
        "FlextInfraRefactorClassNestingTransformer": (
            "flext_infra.transformers.class_nesting",
            "FlextInfraRefactorClassNestingTransformer",
        ),
        "FlextInfraRefactorClassReconstructor": (
            "flext_infra.transformers.class_reconstructor",
            "FlextInfraRefactorClassReconstructor",
        ),
        "FlextInfraRefactorClassReconstructorRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorClassReconstructorRule",
        ),
        "FlextInfraRefactorDeprecatedRemover": (
            "flext_infra.transformers.deprecated_remover",
            "FlextInfraRefactorDeprecatedRemover",
        ),
        "FlextInfraRefactorEngine": (
            "flext_infra.refactor.engine",
            "FlextInfraRefactorEngine",
        ),
        "FlextInfraRefactorEngineHelpersMixin": (
            "flext_infra.refactor._engine_helpers",
            "FlextInfraRefactorEngineHelpersMixin",
        ),
        "FlextInfraRefactorEnsureFutureAnnotationsRule": (
            "flext_infra.rules.ensure_future_annotations",
            "FlextInfraRefactorEnsureFutureAnnotationsRule",
        ),
        "FlextInfraRefactorImportBypassRemover": (
            "flext_infra.transformers.import_bypass_remover",
            "FlextInfraRefactorImportBypassRemover",
        ),
        "FlextInfraRefactorImportModernizer": (
            "flext_infra.transformers.import_modernizer",
            "FlextInfraRefactorImportModernizer",
        ),
        "FlextInfraRefactorImportModernizerRule": (
            "flext_infra.rules.import_modernizer",
            "FlextInfraRefactorImportModernizerRule",
        ),
        "FlextInfraRefactorLazyImportFixer": (
            "flext_infra.transformers.lazy_import_fixer",
            "FlextInfraRefactorLazyImportFixer",
        ),
        "FlextInfraRefactorLegacyRemovalRule": (
            "flext_infra.rules.legacy_removal",
            "FlextInfraRefactorLegacyRemovalRule",
        ),
        "FlextInfraRefactorLegacyRemovalTextRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorLegacyRemovalTextRule",
        ),
        "FlextInfraRefactorLooseClassScanner": (
            "flext_infra.refactor.scanner",
            "FlextInfraRefactorLooseClassScanner",
        ),
        "FlextInfraRefactorMROClassMigrationRule": (
            "flext_infra.rules.mro_class_migration",
            "FlextInfraRefactorMROClassMigrationRule",
        ),
        "FlextInfraRefactorMROClassMigrationTextRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorMROClassMigrationTextRule",
        ),
        "FlextInfraRefactorMROImportRewriter": (
            "flext_infra.refactor.mro_import_rewriter",
            "FlextInfraRefactorMROImportRewriter",
        ),
        "FlextInfraRefactorMROMigrationValidator": (
            "flext_infra.refactor.mro_migration_validator",
            "FlextInfraRefactorMROMigrationValidator",
        ),
        "FlextInfraRefactorMRORedundancyChecker": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorMRORedundancyChecker",
        ),
        "FlextInfraRefactorMRORemover": (
            "flext_infra.transformers.mro_remover",
            "FlextInfraRefactorMRORemover",
        ),
        "FlextInfraRefactorMROResolver": (
            "flext_infra.refactor.mro_resolver",
            "FlextInfraRefactorMROResolver",
        ),
        "FlextInfraRefactorMROSymbolPropagator": (
            "flext_infra.transformers.mro_symbol_propagator",
            "FlextInfraRefactorMROSymbolPropagator",
        ),
        "FlextInfraRefactorMigrateToClassMRO": (
            "flext_infra.refactor.migrate_to_class_mro",
            "FlextInfraRefactorMigrateToClassMRO",
        ),
        "FlextInfraRefactorPatternCorrectionsRule": (
            "flext_infra.rules.pattern_corrections",
            "FlextInfraRefactorPatternCorrectionsRule",
        ),
        "FlextInfraRefactorPatternCorrectionsTextRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorPatternCorrectionsTextRule",
        ),
        "FlextInfraRefactorRule": (
            "flext_infra.refactor._base_rule",
            "FlextInfraRefactorRule",
        ),
        "FlextInfraRefactorRuleDefinitionValidator": (
            "flext_infra.refactor.rule_definition_validator",
            "FlextInfraRefactorRuleDefinitionValidator",
        ),
        "FlextInfraRefactorRuleLoader": (
            "flext_infra.refactor.rule",
            "FlextInfraRefactorRuleLoader",
        ),
        "FlextInfraRefactorSafetyManager": (
            "flext_infra.refactor.safety",
            "FlextInfraRefactorSafetyManager",
        ),
        "FlextInfraRefactorSignaturePropagationRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorSignaturePropagationRule",
        ),
        "FlextInfraRefactorSignaturePropagator": (
            "flext_infra.transformers.signature_propagator",
            "FlextInfraRefactorSignaturePropagator",
        ),
        "FlextInfraRefactorSymbolPropagationRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorSymbolPropagationRule",
        ),
        "FlextInfraRefactorSymbolPropagator": (
            "flext_infra.transformers.symbol_propagator",
            "FlextInfraRefactorSymbolPropagator",
        ),
        "FlextInfraRefactorTier0ImportFixRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorTier0ImportFixRule",
        ),
        "FlextInfraUtilitiesRefactorTransformerPolicy": (
            "flext_infra._utilities.transformer_policy",
            "FlextInfraUtilitiesRefactorTransformerPolicy",
        ),
        "FlextInfraRefactorTypingAnnotationFixRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorTypingAnnotationFixRule",
        ),
        "FlextInfraRefactorTypingUnificationRule": (
            "flext_infra.refactor._engine_rules",
            "FlextInfraRefactorTypingUnificationRule",
        ),
        "FlextInfraRefactorTypingUnifier": (
            "flext_infra.transformers.typing_unifier",
            "FlextInfraRefactorTypingUnifier",
        ),
        "FlextInfraRefactorViolationAnalyzer": (
            "flext_infra.refactor.violation_analyzer",
            "FlextInfraRefactorViolationAnalyzer",
        ),
        "FlextInfraReleaseOrchestrator": (
            "flext_infra.release.orchestrator",
            "FlextInfraReleaseOrchestrator",
        ),
        "FlextInfraReleaseOrchestratorPhases": (
            "flext_infra.release.orchestrator_phases",
            "FlextInfraReleaseOrchestratorPhases",
        ),
        "FlextInfraRopeTransformer": (
            "flext_infra.transformers._base",
            "FlextInfraRopeTransformer",
        ),
        "FlextInfraRuffFormatGate": (
            "flext_infra.gates.ruff_format",
            "FlextInfraRuffFormatGate",
        ),
        "FlextInfraRuffLintGate": (
            "flext_infra.gates.ruff_lint",
            "FlextInfraRuffLintGate",
        ),
        "FlextInfraRuntimeAliasDetector": (
            "flext_infra.detectors.runtime_alias_detector",
            "FlextInfraRuntimeAliasDetector",
        ),
        "FlextInfraRuntimeDevDependencyDetector": (
            "flext_infra.deps.detector",
            "FlextInfraRuntimeDevDependencyDetector",
        ),
        "FlextInfraScanFileMixin": (
            "flext_infra.detectors._base_detector",
            "FlextInfraScanFileMixin",
        ),
        "FlextInfraServiceBase": ("flext_infra.base", "FlextInfraServiceBase"),
        "FlextInfraServiceBasemkMixin": (
            "flext_infra.services.basemk",
            "FlextInfraServiceBasemkMixin",
        ),
        "FlextInfraServiceCheckMixin": (
            "flext_infra.services.check",
            "FlextInfraServiceCheckMixin",
        ),
        "FlextInfraServiceCodegenMixin": (
            "flext_infra.services.codegen",
            "FlextInfraServiceCodegenMixin",
        ),
        "FlextInfraServiceDepsMixin": (
            "flext_infra.services.deps",
            "FlextInfraServiceDepsMixin",
        ),
        "FlextInfraServiceDocsMixin": (
            "flext_infra.services.docs",
            "FlextInfraServiceDocsMixin",
        ),
        "FlextInfraServiceGithubMixin": (
            "flext_infra.services.github",
            "FlextInfraServiceGithubMixin",
        ),
        "FlextInfraServiceRefactorMixin": (
            "flext_infra.services.refactor",
            "FlextInfraServiceRefactorMixin",
        ),
        "FlextInfraServiceReleaseMixin": (
            "flext_infra.services.release",
            "FlextInfraServiceReleaseMixin",
        ),
        "FlextInfraServiceValidateMixin": (
            "flext_infra.services.validate",
            "FlextInfraServiceValidateMixin",
        ),
        "FlextInfraServiceWorkspaceMixin": (
            "flext_infra.services.workspace",
            "FlextInfraServiceWorkspaceMixin",
        ),
        "FlextInfraSkillValidator": (
            "flext_infra.validate.skill_validator",
            "FlextInfraSkillValidator",
        ),
        "FlextInfraStubSupplyChain": (
            "flext_infra.validate.stub_chain",
            "FlextInfraStubSupplyChain",
        ),
        "FlextInfraSyncService": (
            "flext_infra.workspace.sync",
            "FlextInfraSyncService",
        ),
        "FlextInfraTextPatternScanner": (
            "flext_infra.validate.scanner",
            "FlextInfraTextPatternScanner",
        ),
        "FlextInfraToml": ("flext_infra.services.toml_engine", "FlextInfraToml"),
        "FlextInfraTransformerTier0ImportFixer": (
            "flext_infra.transformers.tier0_import_fixer",
            "FlextInfraTransformerTier0ImportFixer",
        ),
        "FlextInfraTypes": ("flext_infra.typings", "FlextInfraTypes"),
        "FlextInfraTypingAnnotationReplacer": (
            "flext_infra.transformers.typing_annotation_replacer",
            "FlextInfraTypingAnnotationReplacer",
        ),
        "FlextInfraUtilities": ("flext_infra.utilities", "FlextInfraUtilities"),
        "FlextInfraUtilitiesCodegen": (
            "flext_infra._utilities.codegen",
            "FlextInfraUtilitiesCodegen",
        ),
        "FlextInfraUtilitiesImportNormalizer": (
            "flext_infra._utilities.import_normalizer",
            "FlextInfraUtilitiesImportNormalizer",
        ),
        "FlextInfraUtilitiesRefactor": (
            "flext_infra._utilities._utilities",
            "FlextInfraUtilitiesRefactor",
        ),
        "FlextInfraUtilitiesRefactorCensus": (
            "flext_infra._utilities._utilities_census",
            "FlextInfraUtilitiesRefactorCensus",
        ),
        "FlextInfraUtilitiesRefactorCli": (
            "flext_infra._utilities._utilities_cli",
            "FlextInfraUtilitiesRefactorCli",
        ),
        "FlextInfraUtilitiesRefactorEngine": (
            "flext_infra._utilities._utilities_engine",
            "FlextInfraUtilitiesRefactorEngine",
        ),
        "FlextInfraUtilitiesRefactorMroScan": (
            "flext_infra._utilities._utilities_mro_scan",
            "FlextInfraUtilitiesRefactorMroScan",
        ),
        "FlextInfraUtilitiesRefactorMroTransform": (
            "flext_infra._utilities._utilities_mro_transform",
            "FlextInfraUtilitiesRefactorMroTransform",
        ),
        "FlextInfraUtilitiesRefactorNamespace": (
            "flext_infra._utilities._utilities_namespace",
            "FlextInfraUtilitiesRefactorNamespace",
        ),
        "FlextInfraUtilitiesRefactorNamespaceCommon": (
            "flext_infra._utilities._utilities_namespace_analysis",
            "FlextInfraUtilitiesRefactorNamespaceCommon",
        ),
        "FlextInfraUtilitiesRefactorNamespaceFacades": (
            "flext_infra._utilities._utilities_namespace_facades",
            "FlextInfraUtilitiesRefactorNamespaceFacades",
        ),
        "FlextInfraUtilitiesRefactorNamespaceMoves": (
            "flext_infra._utilities._utilities_namespace_moves",
            "FlextInfraUtilitiesRefactorNamespaceMoves",
        ),
        "FlextInfraUtilitiesRefactorNamespaceMro": (
            "flext_infra._utilities._utilities_namespace_analysis",
            "FlextInfraUtilitiesRefactorNamespaceMro",
        ),
        "FlextInfraUtilitiesRefactorNamespaceRuntime": (
            "flext_infra._utilities._utilities_namespace_runtime",
            "FlextInfraUtilitiesRefactorNamespaceRuntime",
        ),
        "FlextInfraUtilitiesRefactorPolicy": (
            "flext_infra._utilities._utilities_policy",
            "FlextInfraUtilitiesRefactorPolicy",
        ),
        "FlextInfraUtilitiesRefactorPydantic": (
            "flext_infra._utilities._utilities_pydantic",
            "FlextInfraUtilitiesRefactorPydantic",
        ),
        "FlextInfraUtilitiesRefactorPydanticAnalysis": (
            "flext_infra._utilities._utilities_pydantic_analysis",
            "FlextInfraUtilitiesRefactorPydanticAnalysis",
        ),
        "FlextInfraVersion": ("flext_infra.__version__", "FlextInfraVersion"),
        "FlextInfraViolationCensusVisitor": (
            "flext_infra.transformers.violation_census_visitor",
            "FlextInfraViolationCensusVisitor",
        ),
        "FlextInfraWorkspaceCheckGatesMixin": (
            "flext_infra.check._workspace_check_gates",
            "FlextInfraWorkspaceCheckGatesMixin",
        ),
        "FlextInfraWorkspaceChecker": (
            "flext_infra.check.workspace_check",
            "FlextInfraWorkspaceChecker",
        ),
        "FlextInfraWorkspaceCheckerCli": (
            "flext_infra.check.workspace_check_cli",
            "FlextInfraWorkspaceCheckerCli",
        ),
        "FlextInfraWorkspaceDetector": (
            "flext_infra.workspace.detector",
            "FlextInfraWorkspaceDetector",
        ),
        "FlextInfraWorkspaceMakefileGenerator": (
            "flext_infra.workspace.workspace_makefile",
            "FlextInfraWorkspaceMakefileGenerator",
        ),
        "__author__": ("flext_infra.__version__", "__author__"),
        "__author_email__": ("flext_infra.__version__", "__author_email__"),
        "__description__": ("flext_infra.__version__", "__description__"),
        "__license__": ("flext_infra.__version__", "__license__"),
        "__title__": ("flext_infra.__version__", "__title__"),
        "__url__": ("flext_infra.__version__", "__url__"),
        "__version__": ("flext_infra.__version__", "__version__"),
        "__version_info__": ("flext_infra.__version__", "__version_info__"),
        "_constants": "flext_infra._constants",
        "_models": "flext_infra._models",
        "_protocols": "flext_infra._protocols",
        "_typings": "flext_infra._typings",
        "_utilities": "flext_infra._utilities",
        "api": "flext_infra.api",
        "base": "flext_infra.base",
        "build_parser": ("flext_infra.check.workspace_check", "build_parser"),
        "c": ("flext_infra.constants", "FlextInfraConstants"),
        "cli": "flext_infra.cli",
        "constants": "flext_infra.constants",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "h": ("flext_core.handlers", "FlextHandlers"),
        "infra": ("flext_infra.api", "infra"),
        "logger": ("flext_infra.workspace.maintenance.python_version", "logger"),
        "m": ("flext_infra.models", "FlextInfraModels"),
        "main": ("flext_infra.cli", "main"),
        "models": "flext_infra.models",
        "p": ("flext_infra.protocols", "FlextInfraProtocols"),
        "protocols": "flext_infra.protocols",
        "r": ("flext_core.result", "FlextResult"),
        "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
        "s": ("flext_infra.base", "s"),
        "t": ("flext_infra.typings", "FlextInfraTypes"),
        "typings": "flext_infra.typings",
        "u": ("flext_infra.utilities", "FlextInfraUtilities"),
        "utilities": "flext_infra.utilities",
    },
)
_ = _LAZY_IMPORTS.pop("cleanup_submodule_namespace", None)
_ = _LAZY_IMPORTS.pop("install_lazy_exports", None)
_ = _LAZY_IMPORTS.pop("lazy_getattr", None)
_ = _LAZY_IMPORTS.pop("merge_lazy_imports", None)
_ = _LAZY_IMPORTS.pop("output", None)
_ = _LAZY_IMPORTS.pop("output_reporting", None)

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
    "FlextInfraCommandContext",
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
    "FlextInfraConstantsCore",
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
    "_constants",
    "_models",
    "_protocols",
    "_typings",
    "_utilities",
    "api",
    "base",
    "build_parser",
    "c",
    "cli",
    "constants",
    "d",
    "e",
    "h",
    "infra",
    "logger",
    "m",
    "main",
    "models",
    "p",
    "protocols",
    "r",
    "run_cli",
    "s",
    "t",
    "typings",
    "u",
    "utilities",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
