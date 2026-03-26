# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Public API for flext-infra.

Provides access to infrastructure services for workspace management, validation,
dependency handling, and build orchestration in the FLEXT ecosystem.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes, d, e, h, r, s, x

    from flext_infra import (
        _constants,
        _models,
        _protocols,
        _typings,
        _utilities,
        basemk,
        check,
        codegen,
        deps,
        detectors,
        docs,
        gates,
        refactor,
        release,
        rules,
        transformers,
        validate,
        workspace,
    )
    from flext_infra.__version__ import (
        __all__,
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
    from flext_infra._constants.rope import FlextInfraConstantsRope
    from flext_infra._models.base import FlextInfraModelsBase
    from flext_infra._models.rope import FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan
    from flext_infra._protocols.base import FlextInfraProtocolsBase
    from flext_infra._protocols.rope import FlextInfraProtocolsRope
    from flext_infra._typings.base import FlextInfraTypesBase
    from flext_infra._typings.rope import FlextInfraTypesRope
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.cli import FlextInfraUtilitiesCli
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
    from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
    from flext_infra._utilities.git import FlextInfraUtilitiesGit
    from flext_infra._utilities.github import FlextInfraUtilitiesGithub
    from flext_infra._utilities.io import FlextInfraUtilitiesIo
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.output import FlextInfraUtilitiesOutput, output
    from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
    from flext_infra._utilities.paths import FlextInfraUtilitiesPaths
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease
    from flext_infra._utilities.reporting import FlextInfraUtilitiesReporting
    from flext_infra._utilities.rope import FlextInfraUtilitiesRope
    from flext_infra._utilities.rope_hooks import (
        register_rope_hooks,
        run_mro_migration_hook,
    )
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
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
    from flext_infra.check._constants import FlextInfraCheckConstants
    from flext_infra.check._models import FlextInfraCheckModels
    from flext_infra.check.services import (
        FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check import build_parser, main, run_cli
    from flext_infra.codegen._codegen_coercion import FlextInfraCodegenCoercion
    from flext_infra.codegen._codegen_execution_tools import (
        FlextInfraCodegenExecutionTools,
    )
    from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration
    from flext_infra.codegen._codegen_metrics import FlextInfraCodegenMetrics
    from flext_infra.codegen._codegen_metrics_checks import (
        FlextInfraCodegenMetricsChecks,
    )
    from flext_infra.codegen._codegen_snapshot import FlextInfraCodegenSnapshot
    from flext_infra.codegen._constants import FlextInfraCodegenConstants
    from flext_infra.codegen._models import FlextInfraCodegenModels
    from flext_infra.codegen._utilities import FlextInfraUtilitiesCodegen
    from flext_infra.codegen._utilities_codegen_ast_parsing import (
        FlextInfraUtilitiesCodegenAstParsing,
    )
    from flext_infra.codegen._utilities_codegen_constant_transformer import (
        FlextInfraUtilitiesCodegenConstantTransformation,
    )
    from flext_infra.codegen._utilities_codegen_constant_visitor import (
        FlextInfraUtilitiesCodegenConstantDetection,
    )
    from flext_infra.codegen._utilities_codegen_execution import (
        FlextInfraUtilitiesCodegenExecution,
    )
    from flext_infra.codegen._utilities_codegen_governance import (
        FlextInfraUtilitiesCodegenGovernance,
    )
    from flext_infra.codegen._utilities_transforms import (
        FlextInfraUtilitiesCodegenTransforms,
    )
    from flext_infra.codegen.census import FlextInfraCodegenCensus
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
    from flext_infra.deps._models import FlextInfraDepsModels
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
    from flext_infra.deps._phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
    from flext_infra.deps._phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from flext_infra.deps._phases.inject_comments import FlextInfraInjectCommentsPhase
    from flext_infra.deps.detection import FlextInfraDependencyDetectionService
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
    from flext_infra.deps.path_sync import FlextInfraDependencyPathSync
    from flext_infra.detectors._base_detector import FlextInfraScanFileMixin
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
    from flext_infra.detectors.import_collector import FlextInfraImportCollector
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
    from flext_infra.docs._constants import FlextInfraDocsConstants
    from flext_infra.docs._models import FlextInfraDocsModels
    from flext_infra.docs.auditor import FlextInfraDocAuditor
    from flext_infra.docs.builder import FlextInfraDocBuilder
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
    from flext_infra.refactor._function_dependency_collector import (
        FlextInfraFunctionDependencyCollector,
    )
    from flext_infra.refactor._import_dependency_collector import (
        FlextInfraImportDependencyCollector,
    )
    from flext_infra.refactor._models import FlextInfraRefactorModels
    from flext_infra.refactor._models_ast_grep import FlextInfraRefactorAstGrepModels
    from flext_infra.refactor._models_namespace_enforcer import (
        FlextInfraNamespaceEnforcerModels,
    )
    from flext_infra.refactor._post_check_gate import FlextInfraPostCheckGate
    from flext_infra.refactor._top_level_class_collector import (
        FlextInfraTopLevelClassCollector,
    )
    from flext_infra.refactor._typings import FlextInfraRectorTypes
    from flext_infra.refactor._utilities import FlextInfraUtilitiesRefactor
    from flext_infra.refactor._utilities_cli import FlextInfraUtilitiesRefactorCli
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
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
    from flext_infra.rules.class_nesting import FlextInfraClassNestingRefactorRule
    from flext_infra.rules.class_reconstructor import (
        FlextInfraPreCheckGate,
        FlextInfraRefactorClassNestingReconstructor,
        FlextInfraRefactorClassReconstructorRule,
    )
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
    from flext_infra.rules.mro_redundancy_checker import (
        FlextInfraRefactorMRORedundancyChecker,
    )
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule,
    )
    from flext_infra.rules.symbol_propagation import (
        FlextInfraRefactorSignaturePropagationRule,
        FlextInfraRefactorSignaturePropagator,
        FlextInfraRefactorSymbolPropagationRule,
    )
    from flext_infra.rules.tier0_import_fix import FlextInfraRefactorTier0ImportFixRule
    from flext_infra.rules.type_alias_unification import (
        FlextInfraRefactorTypingUnificationRule,
    )
    from flext_infra.rules.typing_census import (
        FlextInfraRefactorTypingAnnotationFixRule,
    )
    from flext_infra.transformers._base import FlextInfraChangeTrackingTransformer
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
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
    from flext_infra.workspace import maintenance
    from flext_infra.workspace._constants import FlextInfraWorkspaceConstants
    from flext_infra.workspace._models import FlextInfraWorkspaceModels
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMode,
    )
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

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "CONTAINER_DICT_SEQ_ADAPTER": [
        "flext_infra.refactor._base_rule",
        "CONTAINER_DICT_SEQ_ADAPTER",
    ],
    "FlextInfraBanditGate": ["flext_infra.gates.bandit", "FlextInfraBanditGate"],
    "FlextInfraBaseMkGenerator": [
        "flext_infra.basemk.generator",
        "FlextInfraBaseMkGenerator",
    ],
    "FlextInfraBaseMkTemplateEngine": [
        "flext_infra.basemk.engine",
        "FlextInfraBaseMkTemplateEngine",
    ],
    "FlextInfraBaseMkValidator": [
        "flext_infra.validate.basemk_validator",
        "FlextInfraBaseMkValidator",
    ],
    "FlextInfraBasemkConstants": [
        "flext_infra.basemk._constants",
        "FlextInfraBasemkConstants",
    ],
    "FlextInfraBasemkModels": ["flext_infra.basemk._models", "FlextInfraBasemkModels"],
    "FlextInfraCensusImportDiscoveryVisitor": [
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusImportDiscoveryVisitor",
    ],
    "FlextInfraCensusUsageCollector": [
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusUsageCollector",
    ],
    "FlextInfraChangeTracker": [
        "flext_infra.refactor._base_rule",
        "FlextInfraChangeTracker",
    ],
    "FlextInfraChangeTrackingTransformer": [
        "flext_infra.transformers._base",
        "FlextInfraChangeTrackingTransformer",
    ],
    "FlextInfraCheckConstants": [
        "flext_infra.check._constants",
        "FlextInfraCheckConstants",
    ],
    "FlextInfraCheckModels": ["flext_infra.check._models", "FlextInfraCheckModels"],
    "FlextInfraClassNestingRefactorRule": [
        "flext_infra.rules.class_nesting",
        "FlextInfraClassNestingRefactorRule",
    ],
    "FlextInfraClassPlacementDetector": [
        "flext_infra.detectors.class_placement_detector",
        "FlextInfraClassPlacementDetector",
    ],
    "FlextInfraCodegenCensus": [
        "flext_infra.codegen.census",
        "FlextInfraCodegenCensus",
    ],
    "FlextInfraCodegenCoercion": [
        "flext_infra.codegen._codegen_coercion",
        "FlextInfraCodegenCoercion",
    ],
    "FlextInfraCodegenConstants": [
        "flext_infra.codegen._constants",
        "FlextInfraCodegenConstants",
    ],
    "FlextInfraCodegenConstantsQualityGate": [
        "flext_infra.codegen.constants_quality_gate",
        "FlextInfraCodegenConstantsQualityGate",
    ],
    "FlextInfraCodegenExecutionTools": [
        "flext_infra.codegen._codegen_execution_tools",
        "FlextInfraCodegenExecutionTools",
    ],
    "FlextInfraCodegenFixer": ["flext_infra.codegen.fixer", "FlextInfraCodegenFixer"],
    "FlextInfraCodegenGeneration": [
        "flext_infra.codegen._codegen_generation",
        "FlextInfraCodegenGeneration",
    ],
    "FlextInfraCodegenLazyInit": [
        "flext_infra.codegen.lazy_init",
        "FlextInfraCodegenLazyInit",
    ],
    "FlextInfraCodegenMetrics": [
        "flext_infra.codegen._codegen_metrics",
        "FlextInfraCodegenMetrics",
    ],
    "FlextInfraCodegenMetricsChecks": [
        "flext_infra.codegen._codegen_metrics_checks",
        "FlextInfraCodegenMetricsChecks",
    ],
    "FlextInfraCodegenModels": [
        "flext_infra.codegen._models",
        "FlextInfraCodegenModels",
    ],
    "FlextInfraCodegenPyTyped": [
        "flext_infra.codegen.py_typed",
        "FlextInfraCodegenPyTyped",
    ],
    "FlextInfraCodegenScaffolder": [
        "flext_infra.codegen.scaffolder",
        "FlextInfraCodegenScaffolder",
    ],
    "FlextInfraCodegenSnapshot": [
        "flext_infra.codegen._codegen_snapshot",
        "FlextInfraCodegenSnapshot",
    ],
    "FlextInfraCompatibilityAliasDetector": [
        "flext_infra.detectors.compatibility_alias_detector",
        "FlextInfraCompatibilityAliasDetector",
    ],
    "FlextInfraConfigFixer": ["flext_infra.check.services", "FlextInfraConfigFixer"],
    "FlextInfraConsolidateGroupsPhase": [
        "flext_infra.deps._phases.consolidate_groups",
        "FlextInfraConsolidateGroupsPhase",
    ],
    "FlextInfraConstants": ["flext_infra.constants", "FlextInfraConstants"],
    "FlextInfraConstantsBase": [
        "flext_infra._constants.base",
        "FlextInfraConstantsBase",
    ],
    "FlextInfraConstantsRope": [
        "flext_infra._constants.rope",
        "FlextInfraConstantsRope",
    ],
    "FlextInfraCoreConstants": [
        "flext_infra.validate._constants",
        "FlextInfraCoreConstants",
    ],
    "FlextInfraCoreModels": ["flext_infra.validate._models", "FlextInfraCoreModels"],
    "FlextInfraCyclicImportDetector": [
        "flext_infra.detectors.cyclic_import_detector",
        "FlextInfraCyclicImportDetector",
    ],
    "FlextInfraDependencyAnalyzer": [
        "flext_infra.detectors.dependency_analyzer_base",
        "FlextInfraDependencyAnalyzer",
    ],
    "FlextInfraDependencyDetectionService": [
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionService",
    ],
    "FlextInfraDependencyDetectorRuntime": [
        "flext_infra.deps._detector_runtime",
        "FlextInfraDependencyDetectorRuntime",
    ],
    "FlextInfraDependencyPathSync": [
        "flext_infra.deps.path_sync",
        "FlextInfraDependencyPathSync",
    ],
    "FlextInfraDepsConstants": [
        "flext_infra.deps._constants",
        "FlextInfraDepsConstants",
    ],
    "FlextInfraDepsModels": ["flext_infra.deps._models", "FlextInfraDepsModels"],
    "FlextInfraDocAuditor": ["flext_infra.docs.auditor", "FlextInfraDocAuditor"],
    "FlextInfraDocBuilder": ["flext_infra.docs.builder", "FlextInfraDocBuilder"],
    "FlextInfraDocFixer": ["flext_infra.docs.fixer", "FlextInfraDocFixer"],
    "FlextInfraDocGenerator": ["flext_infra.docs.generator", "FlextInfraDocGenerator"],
    "FlextInfraDocValidator": ["flext_infra.docs.validator", "FlextInfraDocValidator"],
    "FlextInfraDocsConstants": [
        "flext_infra.docs._constants",
        "FlextInfraDocsConstants",
    ],
    "FlextInfraDocsModels": ["flext_infra.docs._models", "FlextInfraDocsModels"],
    "FlextInfraEnsureCoverageConfigPhase": [
        "flext_infra.deps._phases.ensure_coverage",
        "FlextInfraEnsureCoverageConfigPhase",
    ],
    "FlextInfraEnsureExtraPathsPhase": [
        "flext_infra.deps._phases.ensure_extra_paths",
        "FlextInfraEnsureExtraPathsPhase",
    ],
    "FlextInfraEnsureFormattingToolingPhase": [
        "flext_infra.deps._phases.ensure_formatting",
        "FlextInfraEnsureFormattingToolingPhase",
    ],
    "FlextInfraEnsureMypyConfigPhase": [
        "flext_infra.deps._phases.ensure_mypy",
        "FlextInfraEnsureMypyConfigPhase",
    ],
    "FlextInfraEnsureNamespaceToolingPhase": [
        "flext_infra.deps._phases.ensure_namespace",
        "FlextInfraEnsureNamespaceToolingPhase",
    ],
    "FlextInfraEnsurePydanticMypyConfigPhase": [
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "FlextInfraEnsurePydanticMypyConfigPhase",
    ],
    "FlextInfraEnsurePyreflyConfigPhase": [
        "flext_infra.deps._phases.ensure_pyrefly",
        "FlextInfraEnsurePyreflyConfigPhase",
    ],
    "FlextInfraEnsurePyrightConfigPhase": [
        "flext_infra.deps._phases.ensure_pyright",
        "FlextInfraEnsurePyrightConfigPhase",
    ],
    "FlextInfraEnsurePytestConfigPhase": [
        "flext_infra.deps._phases.ensure_pytest",
        "FlextInfraEnsurePytestConfigPhase",
    ],
    "FlextInfraEnsureRuffConfigPhase": [
        "flext_infra.deps._phases.ensure_ruff",
        "FlextInfraEnsureRuffConfigPhase",
    ],
    "FlextInfraExtraPathsManager": [
        "flext_infra.deps.extra_paths",
        "FlextInfraExtraPathsManager",
    ],
    "FlextInfraFunctionDependencyCollector": [
        "flext_infra.refactor._function_dependency_collector",
        "FlextInfraFunctionDependencyCollector",
    ],
    "FlextInfraFutureAnnotationsDetector": [
        "flext_infra.detectors.future_annotations_detector",
        "FlextInfraFutureAnnotationsDetector",
    ],
    "FlextInfraGate": ["flext_infra.gates._base_gate", "FlextInfraGate"],
    "FlextInfraGateRegistry": [
        "flext_infra.gates._gate_registry",
        "FlextInfraGateRegistry",
    ],
    "FlextInfraGatesModels": ["flext_infra.gates._models", "FlextInfraGatesModels"],
    "FlextInfraGenericTransformerRule": [
        "flext_infra.refactor._base_rule",
        "FlextInfraGenericTransformerRule",
    ],
    "FlextInfraGithubConstants": [
        "flext_infra.github._constants",
        "FlextInfraGithubConstants",
    ],
    "FlextInfraGithubModels": ["flext_infra.github._models", "FlextInfraGithubModels"],
    "FlextInfraGoGate": ["flext_infra.gates.go", "FlextInfraGoGate"],
    "FlextInfraHelperConsolidationTransformer": [
        "flext_infra.transformers.helper_consolidation",
        "FlextInfraHelperConsolidationTransformer",
    ],
    "FlextInfraImportAliasDetector": [
        "flext_infra.detectors.import_alias_detector",
        "FlextInfraImportAliasDetector",
    ],
    "FlextInfraImportCollector": [
        "flext_infra.detectors.import_collector",
        "FlextInfraImportCollector",
    ],
    "FlextInfraImportDependencyCollector": [
        "flext_infra.refactor._import_dependency_collector",
        "FlextInfraImportDependencyCollector",
    ],
    "FlextInfraInjectCommentsPhase": [
        "flext_infra.deps._phases.inject_comments",
        "FlextInfraInjectCommentsPhase",
    ],
    "FlextInfraInternalDependencySyncService": [
        "flext_infra.deps.internal_sync",
        "FlextInfraInternalDependencySyncService",
    ],
    "FlextInfraInternalImportDetector": [
        "flext_infra.detectors.internal_import_detector",
        "FlextInfraInternalImportDetector",
    ],
    "FlextInfraInventoryService": [
        "flext_infra.validate.inventory",
        "FlextInfraInventoryService",
    ],
    "FlextInfraLooseObjectDetector": [
        "flext_infra.detectors.loose_object_detector",
        "FlextInfraLooseObjectDetector",
    ],
    "FlextInfraMROCompletenessDetector": [
        "flext_infra.detectors.mro_completeness_detector",
        "FlextInfraMROCompletenessDetector",
    ],
    "FlextInfraManualProtocolDetector": [
        "flext_infra.detectors.manual_protocol_detector",
        "FlextInfraManualProtocolDetector",
    ],
    "FlextInfraManualTypingAliasDetector": [
        "flext_infra.detectors.manual_typing_alias_detector",
        "FlextInfraManualTypingAliasDetector",
    ],
    "FlextInfraMarkdownGate": ["flext_infra.gates.markdown", "FlextInfraMarkdownGate"],
    "FlextInfraModels": ["flext_infra.models", "FlextInfraModels"],
    "FlextInfraModelsBase": ["flext_infra._models.base", "FlextInfraModelsBase"],
    "FlextInfraModelsRope": ["flext_infra._models.rope", "FlextInfraModelsRope"],
    "FlextInfraModelsScan": ["flext_infra._models.scan", "FlextInfraModelsScan"],
    "FlextInfraMypyGate": ["flext_infra.gates.mypy", "FlextInfraMypyGate"],
    "FlextInfraNamespaceEnforcer": [
        "flext_infra.refactor.namespace_enforcer",
        "FlextInfraNamespaceEnforcer",
    ],
    "FlextInfraNamespaceEnforcerModels": [
        "flext_infra.refactor._models_namespace_enforcer",
        "FlextInfraNamespaceEnforcerModels",
    ],
    "FlextInfraNamespaceFacadeScanner": [
        "flext_infra.detectors.namespace_facade_scanner",
        "FlextInfraNamespaceFacadeScanner",
    ],
    "FlextInfraNamespaceSourceDetector": [
        "flext_infra.detectors.namespace_source_detector",
        "FlextInfraNamespaceSourceDetector",
    ],
    "FlextInfraNamespaceValidator": [
        "flext_infra.validate.namespace_validator",
        "FlextInfraNamespaceValidator",
    ],
    "FlextInfraNestedClassPropagationTransformer": [
        "flext_infra.transformers.nested_class_propagation",
        "FlextInfraNestedClassPropagationTransformer",
    ],
    "FlextInfraNormalizerContext": [
        "flext_infra.transformers._utilities_normalizer",
        "FlextInfraNormalizerContext",
    ],
    "FlextInfraOrchestratorService": [
        "flext_infra.workspace.orchestrator",
        "FlextInfraOrchestratorService",
    ],
    "FlextInfraPostCheckGate": [
        "flext_infra.refactor._post_check_gate",
        "FlextInfraPostCheckGate",
    ],
    "FlextInfraPreCheckGate": [
        "flext_infra.rules.class_reconstructor",
        "FlextInfraPreCheckGate",
    ],
    "FlextInfraProjectClassifier": [
        "flext_infra.refactor.project_classifier",
        "FlextInfraProjectClassifier",
    ],
    "FlextInfraProjectMakefileUpdater": [
        "flext_infra.workspace.project_makefile",
        "FlextInfraProjectMakefileUpdater",
    ],
    "FlextInfraProjectMigrator": [
        "flext_infra.workspace.migrator",
        "FlextInfraProjectMigrator",
    ],
    "FlextInfraProtocols": ["flext_infra.protocols", "FlextInfraProtocols"],
    "FlextInfraProtocolsBase": [
        "flext_infra._protocols.base",
        "FlextInfraProtocolsBase",
    ],
    "FlextInfraProtocolsRope": [
        "flext_infra._protocols.rope",
        "FlextInfraProtocolsRope",
    ],
    "FlextInfraPyprojectModernizer": [
        "flext_infra.deps.modernizer",
        "FlextInfraPyprojectModernizer",
    ],
    "FlextInfraPyreflyGate": ["flext_infra.gates.pyrefly", "FlextInfraPyreflyGate"],
    "FlextInfraPyrightGate": ["flext_infra.gates.pyright", "FlextInfraPyrightGate"],
    "FlextInfraPytestDiagExtractor": [
        "flext_infra.validate.pytest_diag",
        "FlextInfraPytestDiagExtractor",
    ],
    "FlextInfraPythonVersionEnforcer": [
        "flext_infra.workspace.maintenance.python_version",
        "FlextInfraPythonVersionEnforcer",
    ],
    "FlextInfraRectorTypes": ["flext_infra.refactor._typings", "FlextInfraRectorTypes"],
    "FlextInfraRefactorAliasRemover": [
        "flext_infra.transformers.alias_remover",
        "FlextInfraRefactorAliasRemover",
    ],
    "FlextInfraRefactorAstGrepModels": [
        "flext_infra.refactor._models_ast_grep",
        "FlextInfraRefactorAstGrepModels",
    ],
    "FlextInfraRefactorCensus": [
        "flext_infra.refactor.census",
        "FlextInfraRefactorCensus",
    ],
    "FlextInfraRefactorClassNestingAnalyzer": [
        "flext_infra.refactor.class_nesting_analyzer",
        "FlextInfraRefactorClassNestingAnalyzer",
    ],
    "FlextInfraRefactorClassNestingReconstructor": [
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassNestingReconstructor",
    ],
    "FlextInfraRefactorClassNestingTransformer": [
        "flext_infra.transformers.class_nesting",
        "FlextInfraRefactorClassNestingTransformer",
    ],
    "FlextInfraRefactorClassReconstructor": [
        "flext_infra.transformers.class_reconstructor",
        "FlextInfraRefactorClassReconstructor",
    ],
    "FlextInfraRefactorClassReconstructorRule": [
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassReconstructorRule",
    ],
    "FlextInfraRefactorConstants": [
        "flext_infra.refactor._constants",
        "FlextInfraRefactorConstants",
    ],
    "FlextInfraRefactorDeprecatedRemover": [
        "flext_infra.transformers.deprecated_remover",
        "FlextInfraRefactorDeprecatedRemover",
    ],
    "FlextInfraRefactorEngine": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorEngine",
    ],
    "FlextInfraRefactorEnsureFutureAnnotationsRule": [
        "flext_infra.rules.ensure_future_annotations",
        "FlextInfraRefactorEnsureFutureAnnotationsRule",
    ],
    "FlextInfraRefactorImportBypassRemover": [
        "flext_infra.transformers.import_bypass_remover",
        "FlextInfraRefactorImportBypassRemover",
    ],
    "FlextInfraRefactorImportModernizer": [
        "flext_infra.transformers.import_modernizer",
        "FlextInfraRefactorImportModernizer",
    ],
    "FlextInfraRefactorImportModernizerRule": [
        "flext_infra.rules.import_modernizer",
        "FlextInfraRefactorImportModernizerRule",
    ],
    "FlextInfraRefactorLazyImportFixer": [
        "flext_infra.transformers.lazy_import_fixer",
        "FlextInfraRefactorLazyImportFixer",
    ],
    "FlextInfraRefactorLegacyRemovalRule": [
        "flext_infra.rules.legacy_removal",
        "FlextInfraRefactorLegacyRemovalRule",
    ],
    "FlextInfraRefactorLooseClassScanner": [
        "flext_infra.refactor.scanner",
        "FlextInfraRefactorLooseClassScanner",
    ],
    "FlextInfraRefactorMROClassMigrationRule": [
        "flext_infra.rules.mro_class_migration",
        "FlextInfraRefactorMROClassMigrationRule",
    ],
    "FlextInfraRefactorMROImportRewriter": [
        "flext_infra.refactor.mro_import_rewriter",
        "FlextInfraRefactorMROImportRewriter",
    ],
    "FlextInfraRefactorMROMigrationValidator": [
        "flext_infra.refactor.mro_migration_validator",
        "FlextInfraRefactorMROMigrationValidator",
    ],
    "FlextInfraRefactorMROPrivateInlineTransformer": [
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROPrivateInlineTransformer",
    ],
    "FlextInfraRefactorMROQualifiedReferenceTransformer": [
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROQualifiedReferenceTransformer",
    ],
    "FlextInfraRefactorMRORedundancyChecker": [
        "flext_infra.rules.mro_redundancy_checker",
        "FlextInfraRefactorMRORedundancyChecker",
    ],
    "FlextInfraRefactorMRORemover": [
        "flext_infra.transformers.mro_remover",
        "FlextInfraRefactorMRORemover",
    ],
    "FlextInfraRefactorMROResolver": [
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROResolver",
    ],
    "FlextInfraRefactorMROSymbolPropagator": [
        "flext_infra.transformers.mro_symbol_propagator",
        "FlextInfraRefactorMROSymbolPropagator",
    ],
    "FlextInfraRefactorMigrateToClassMRO": [
        "flext_infra.refactor.migrate_to_class_mro",
        "FlextInfraRefactorMigrateToClassMRO",
    ],
    "FlextInfraRefactorModels": [
        "flext_infra.refactor._models",
        "FlextInfraRefactorModels",
    ],
    "FlextInfraRefactorPatternCorrectionsRule": [
        "flext_infra.rules.pattern_corrections",
        "FlextInfraRefactorPatternCorrectionsRule",
    ],
    "FlextInfraRefactorRule": [
        "flext_infra.refactor._base_rule",
        "FlextInfraRefactorRule",
    ],
    "FlextInfraRefactorRuleDefinitionValidator": [
        "flext_infra.refactor.rule_definition_validator",
        "FlextInfraRefactorRuleDefinitionValidator",
    ],
    "FlextInfraRefactorRuleLoader": [
        "flext_infra.refactor.rule",
        "FlextInfraRefactorRuleLoader",
    ],
    "FlextInfraRefactorSafetyManager": [
        "flext_infra.refactor.safety",
        "FlextInfraRefactorSafetyManager",
    ],
    "FlextInfraRefactorSignaturePropagationRule": [
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSignaturePropagationRule",
    ],
    "FlextInfraRefactorSignaturePropagator": [
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSignaturePropagator",
    ],
    "FlextInfraRefactorSymbolPropagationRule": [
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSymbolPropagationRule",
    ],
    "FlextInfraRefactorSymbolPropagator": [
        "flext_infra.transformers.symbol_propagator",
        "FlextInfraRefactorSymbolPropagator",
    ],
    "FlextInfraRefactorTier0ImportFixRule": [
        "flext_infra.rules.tier0_import_fix",
        "FlextInfraRefactorTier0ImportFixRule",
    ],
    "FlextInfraRefactorTransformerPolicyUtilities": [
        "flext_infra.transformers.policy",
        "FlextInfraRefactorTransformerPolicyUtilities",
    ],
    "FlextInfraRefactorTypingAnnotationFixRule": [
        "flext_infra.rules.typing_census",
        "FlextInfraRefactorTypingAnnotationFixRule",
    ],
    "FlextInfraRefactorTypingUnificationRule": [
        "flext_infra.rules.type_alias_unification",
        "FlextInfraRefactorTypingUnificationRule",
    ],
    "FlextInfraRefactorTypingUnifier": [
        "flext_infra.transformers.typing_unifier",
        "FlextInfraRefactorTypingUnifier",
    ],
    "FlextInfraRefactorViolationAnalyzer": [
        "flext_infra.refactor.violation_analyzer",
        "FlextInfraRefactorViolationAnalyzer",
    ],
    "FlextInfraReleaseConstants": [
        "flext_infra.release._constants",
        "FlextInfraReleaseConstants",
    ],
    "FlextInfraReleaseModels": [
        "flext_infra.release._models",
        "FlextInfraReleaseModels",
    ],
    "FlextInfraReleaseOrchestrator": [
        "flext_infra.release.orchestrator",
        "FlextInfraReleaseOrchestrator",
    ],
    "FlextInfraRuffFormatGate": [
        "flext_infra.gates.ruff_format",
        "FlextInfraRuffFormatGate",
    ],
    "FlextInfraRuffLintGate": ["flext_infra.gates.ruff_lint", "FlextInfraRuffLintGate"],
    "FlextInfraRuntimeAliasDetector": [
        "flext_infra.detectors.runtime_alias_detector",
        "FlextInfraRuntimeAliasDetector",
    ],
    "FlextInfraRuntimeDevDependencyDetector": [
        "flext_infra.deps.detector",
        "FlextInfraRuntimeDevDependencyDetector",
    ],
    "FlextInfraScanFileMixin": [
        "flext_infra.detectors._base_detector",
        "FlextInfraScanFileMixin",
    ],
    "FlextInfraSharedInfraConstants": [
        "flext_infra.validate._constants",
        "FlextInfraSharedInfraConstants",
    ],
    "FlextInfraSkillValidator": [
        "flext_infra.validate.skill_validator",
        "FlextInfraSkillValidator",
    ],
    "FlextInfraStubSupplyChain": [
        "flext_infra.validate.stub_chain",
        "FlextInfraStubSupplyChain",
    ],
    "FlextInfraSyncService": ["flext_infra.workspace.sync", "FlextInfraSyncService"],
    "FlextInfraTextPatternScanner": [
        "flext_infra.validate.scanner",
        "FlextInfraTextPatternScanner",
    ],
    "FlextInfraTopLevelClassCollector": [
        "flext_infra.refactor._top_level_class_collector",
        "FlextInfraTopLevelClassCollector",
    ],
    "FlextInfraTransformerTier0ImportFixer": [
        "flext_infra.transformers.tier0_import_fixer",
        "FlextInfraTransformerTier0ImportFixer",
    ],
    "FlextInfraTypes": ["flext_infra.typings", "FlextInfraTypes"],
    "FlextInfraTypesBase": ["flext_infra._typings.base", "FlextInfraTypesBase"],
    "FlextInfraTypesRope": ["flext_infra._typings.rope", "FlextInfraTypesRope"],
    "FlextInfraTypingAnnotationReplacer": [
        "flext_infra.transformers.typing_annotation_replacer",
        "FlextInfraTypingAnnotationReplacer",
    ],
    "FlextInfraUtilities": ["flext_infra.utilities", "FlextInfraUtilities"],
    "FlextInfraUtilitiesBase": [
        "flext_infra._utilities.base",
        "FlextInfraUtilitiesBase",
    ],
    "FlextInfraUtilitiesCli": ["flext_infra._utilities.cli", "FlextInfraUtilitiesCli"],
    "FlextInfraUtilitiesCodegen": [
        "flext_infra.codegen._utilities",
        "FlextInfraUtilitiesCodegen",
    ],
    "FlextInfraUtilitiesCodegenAstParsing": [
        "flext_infra.codegen._utilities_codegen_ast_parsing",
        "FlextInfraUtilitiesCodegenAstParsing",
    ],
    "FlextInfraUtilitiesCodegenConstantDetection": [
        "flext_infra.codegen._utilities_codegen_constant_visitor",
        "FlextInfraUtilitiesCodegenConstantDetection",
    ],
    "FlextInfraUtilitiesCodegenConstantTransformation": [
        "flext_infra.codegen._utilities_codegen_constant_transformer",
        "FlextInfraUtilitiesCodegenConstantTransformation",
    ],
    "FlextInfraUtilitiesCodegenExecution": [
        "flext_infra.codegen._utilities_codegen_execution",
        "FlextInfraUtilitiesCodegenExecution",
    ],
    "FlextInfraUtilitiesCodegenGovernance": [
        "flext_infra.codegen._utilities_codegen_governance",
        "FlextInfraUtilitiesCodegenGovernance",
    ],
    "FlextInfraUtilitiesCodegenTransforms": [
        "flext_infra.codegen._utilities_transforms",
        "FlextInfraUtilitiesCodegenTransforms",
    ],
    "FlextInfraUtilitiesDiscovery": [
        "flext_infra._utilities.discovery",
        "FlextInfraUtilitiesDiscovery",
    ],
    "FlextInfraUtilitiesDocs": [
        "flext_infra._utilities.docs",
        "FlextInfraUtilitiesDocs",
    ],
    "FlextInfraUtilitiesFormatting": [
        "flext_infra._utilities.formatting",
        "FlextInfraUtilitiesFormatting",
    ],
    "FlextInfraUtilitiesGit": ["flext_infra._utilities.git", "FlextInfraUtilitiesGit"],
    "FlextInfraUtilitiesGithub": [
        "flext_infra._utilities.github",
        "FlextInfraUtilitiesGithub",
    ],
    "FlextInfraUtilitiesImportNormalizer": [
        "flext_infra.transformers._utilities_normalizer",
        "FlextInfraUtilitiesImportNormalizer",
    ],
    "FlextInfraUtilitiesIo": ["flext_infra._utilities.io", "FlextInfraUtilitiesIo"],
    "FlextInfraUtilitiesIteration": [
        "flext_infra._utilities.iteration",
        "FlextInfraUtilitiesIteration",
    ],
    "FlextInfraUtilitiesLogParser": [
        "flext_infra._utilities.log_parser",
        "FlextInfraUtilitiesLogParser",
    ],
    "FlextInfraUtilitiesOutput": [
        "flext_infra._utilities.output",
        "FlextInfraUtilitiesOutput",
    ],
    "FlextInfraUtilitiesParsing": [
        "flext_infra._utilities.parsing",
        "FlextInfraUtilitiesParsing",
    ],
    "FlextInfraUtilitiesPaths": [
        "flext_infra._utilities.paths",
        "FlextInfraUtilitiesPaths",
    ],
    "FlextInfraUtilitiesPatterns": [
        "flext_infra._utilities.patterns",
        "FlextInfraUtilitiesPatterns",
    ],
    "FlextInfraUtilitiesRefactor": [
        "flext_infra.refactor._utilities",
        "FlextInfraUtilitiesRefactor",
    ],
    "FlextInfraUtilitiesRefactorCli": [
        "flext_infra.refactor._utilities_cli",
        "FlextInfraUtilitiesRefactorCli",
    ],
    "FlextInfraUtilitiesRefactorLoader": [
        "flext_infra.refactor._utilities_loader",
        "FlextInfraUtilitiesRefactorLoader",
    ],
    "FlextInfraUtilitiesRefactorMroScan": [
        "flext_infra.refactor._utilities_mro_scan",
        "FlextInfraUtilitiesRefactorMroScan",
    ],
    "FlextInfraUtilitiesRefactorMroTransform": [
        "flext_infra.refactor._utilities_mro_transform",
        "FlextInfraUtilitiesRefactorMroTransform",
    ],
    "FlextInfraUtilitiesRefactorNamespace": [
        "flext_infra.refactor._utilities_namespace",
        "FlextInfraUtilitiesRefactorNamespace",
    ],
    "FlextInfraUtilitiesRefactorPydantic": [
        "flext_infra.refactor._utilities_pydantic",
        "FlextInfraUtilitiesRefactorPydantic",
    ],
    "FlextInfraUtilitiesRefactorPydanticAnalysis": [
        "flext_infra.refactor._utilities_pydantic_analysis",
        "FlextInfraUtilitiesRefactorPydanticAnalysis",
    ],
    "FlextInfraUtilitiesRelease": [
        "flext_infra._utilities.release",
        "FlextInfraUtilitiesRelease",
    ],
    "FlextInfraUtilitiesReporting": [
        "flext_infra._utilities.reporting",
        "FlextInfraUtilitiesReporting",
    ],
    "FlextInfraUtilitiesRope": [
        "flext_infra._utilities.rope",
        "FlextInfraUtilitiesRope",
    ],
    "FlextInfraUtilitiesSafety": [
        "flext_infra._utilities.safety",
        "FlextInfraUtilitiesSafety",
    ],
    "FlextInfraUtilitiesSelection": [
        "flext_infra._utilities.selection",
        "FlextInfraUtilitiesSelection",
    ],
    "FlextInfraUtilitiesSubprocess": [
        "flext_infra._utilities.subprocess",
        "FlextInfraUtilitiesSubprocess",
    ],
    "FlextInfraUtilitiesTemplates": [
        "flext_infra._utilities.templates",
        "FlextInfraUtilitiesTemplates",
    ],
    "FlextInfraUtilitiesTerminal": [
        "flext_infra._utilities.terminal",
        "FlextInfraUtilitiesTerminal",
    ],
    "FlextInfraUtilitiesToml": [
        "flext_infra._utilities.toml",
        "FlextInfraUtilitiesToml",
    ],
    "FlextInfraUtilitiesTomlParse": [
        "flext_infra._utilities.toml_parse",
        "FlextInfraUtilitiesTomlParse",
    ],
    "FlextInfraUtilitiesVersioning": [
        "flext_infra._utilities.versioning",
        "FlextInfraUtilitiesVersioning",
    ],
    "FlextInfraUtilitiesYaml": [
        "flext_infra._utilities.yaml",
        "FlextInfraUtilitiesYaml",
    ],
    "FlextInfraViolationCensusVisitor": [
        "flext_infra.transformers.violation_census_visitor",
        "FlextInfraViolationCensusVisitor",
    ],
    "FlextInfraWorkspaceChecker": [
        "flext_infra.check.services",
        "FlextInfraWorkspaceChecker",
    ],
    "FlextInfraWorkspaceConstants": [
        "flext_infra.workspace._constants",
        "FlextInfraWorkspaceConstants",
    ],
    "FlextInfraWorkspaceDetector": [
        "flext_infra.workspace.detector",
        "FlextInfraWorkspaceDetector",
    ],
    "FlextInfraWorkspaceMakefileGenerator": [
        "flext_infra.workspace.workspace_makefile",
        "FlextInfraWorkspaceMakefileGenerator",
    ],
    "FlextInfraWorkspaceMode": [
        "flext_infra.workspace.detector",
        "FlextInfraWorkspaceMode",
    ],
    "FlextInfraWorkspaceModels": [
        "flext_infra.workspace._models",
        "FlextInfraWorkspaceModels",
    ],
    "INFRA_MAPPING_ADAPTER": [
        "flext_infra.refactor._base_rule",
        "INFRA_MAPPING_ADAPTER",
    ],
    "INFRA_SEQ_ADAPTER": ["flext_infra.refactor._base_rule", "INFRA_SEQ_ADAPTER"],
    "STR_MAPPING_ADAPTER": ["flext_infra.refactor._base_rule", "STR_MAPPING_ADAPTER"],
    "__all__": ["flext_infra.__version__", "__all__"],
    "__author__": ["flext_infra.__version__", "__author__"],
    "__author_email__": ["flext_infra.__version__", "__author_email__"],
    "__description__": ["flext_infra.__version__", "__description__"],
    "__license__": ["flext_infra.__version__", "__license__"],
    "__title__": ["flext_infra.__version__", "__title__"],
    "__url__": ["flext_infra.__version__", "__url__"],
    "__version__": ["flext_infra.__version__", "__version__"],
    "__version_info__": ["flext_infra.__version__", "__version_info__"],
    "_constants": ["flext_infra._constants", ""],
    "_models": ["flext_infra._models", ""],
    "_protocols": ["flext_infra._protocols", ""],
    "_typings": ["flext_infra._typings", ""],
    "_utilities": ["flext_infra._utilities", ""],
    "basemk": ["flext_infra.basemk", ""],
    "build_parser": ["flext_infra.check.workspace_check", "build_parser"],
    "c": ["flext_infra.constants", "FlextInfraConstants"],
    "check": ["flext_infra.check", ""],
    "codegen": ["flext_infra.codegen", ""],
    "d": ["flext_core", "d"],
    "deps": ["flext_infra.deps", ""],
    "detectors": ["flext_infra.detectors", ""],
    "docs": ["flext_infra.docs", ""],
    "e": ["flext_core", "e"],
    "gates": ["flext_infra.gates", ""],
    "h": ["flext_core", "h"],
    "logger": ["flext_infra.workspace.maintenance.python_version", "logger"],
    "m": ["flext_infra.models", "FlextInfraModels"],
    "main": ["flext_infra.check.workspace_check", "main"],
    "maintenance": ["flext_infra.workspace.maintenance", ""],
    "output": ["flext_infra._utilities.output", "output"],
    "p": ["flext_infra.protocols", "FlextInfraProtocols"],
    "r": ["flext_core", "r"],
    "refactor": ["flext_infra.refactor", ""],
    "register_rope_hooks": ["flext_infra._utilities.rope_hooks", "register_rope_hooks"],
    "release": ["flext_infra.release", ""],
    "rules": ["flext_infra.rules", ""],
    "run_cli": ["flext_infra.check.workspace_check", "run_cli"],
    "run_mro_migration_hook": [
        "flext_infra._utilities.rope_hooks",
        "run_mro_migration_hook",
    ],
    "s": ["flext_core", "s"],
    "t": ["flext_infra.typings", "FlextInfraTypes"],
    "transformers": ["flext_infra.transformers", ""],
    "u": ["flext_infra.utilities", "FlextInfraUtilities"],
    "validate": ["flext_infra.validate", ""],
    "workspace": ["flext_infra.workspace", ""],
    "x": ["flext_core", "x"],
}

__all__ = [
    "CONTAINER_DICT_SEQ_ADAPTER",
    "INFRA_MAPPING_ADAPTER",
    "INFRA_SEQ_ADAPTER",
    "STR_MAPPING_ADAPTER",
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
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenCoercion",
    "FlextInfraCodegenConstants",
    "FlextInfraCodegenConstantsQualityGate",
    "FlextInfraCodegenExecutionTools",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenMetrics",
    "FlextInfraCodegenMetricsChecks",
    "FlextInfraCodegenModels",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenSnapshot",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraConstants",
    "FlextInfraConstantsBase",
    "FlextInfraConstantsRope",
    "FlextInfraCoreConstants",
    "FlextInfraCoreModels",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDependencyAnalyzer",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDependencyPathSync",
    "FlextInfraDepsConstants",
    "FlextInfraDepsModels",
    "FlextInfraDocAuditor",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
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
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraFunctionDependencyCollector",
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
    "FlextInfraImportCollector",
    "FlextInfraImportDependencyCollector",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraInternalImportDetector",
    "FlextInfraInventoryService",
    "FlextInfraLooseObjectDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraMarkdownGate",
    "FlextInfraModels",
    "FlextInfraModelsBase",
    "FlextInfraModelsRope",
    "FlextInfraModelsScan",
    "FlextInfraMypyGate",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerModels",
    "FlextInfraNamespaceFacadeScanner",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraNamespaceValidator",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraNormalizerContext",
    "FlextInfraOrchestratorService",
    "FlextInfraPostCheckGate",
    "FlextInfraPreCheckGate",
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
    "FlextInfraRectorTypes",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorAstGrepModels",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassNestingReconstructor",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorConstants",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorEnsureFutureAnnotationsRule",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorImportModernizerRule",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorLegacyRemovalRule",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROClassMigrationRule",
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
    "FlextInfraRefactorPatternCorrectionsRule",
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
    "FlextInfraTopLevelClassCollector",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypes",
    "FlextInfraTypesBase",
    "FlextInfraTypesRope",
    "FlextInfraTypingAnnotationReplacer",
    "FlextInfraUtilities",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCli",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenAstParsing",
    "FlextInfraUtilitiesCodegenConstantDetection",
    "FlextInfraUtilitiesCodegenConstantTransformation",
    "FlextInfraUtilitiesCodegenExecution",
    "FlextInfraUtilitiesCodegenGovernance",
    "FlextInfraUtilitiesCodegenTransforms",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesImportNormalizer",
    "FlextInfraUtilitiesIo",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCli",
    "FlextInfraUtilitiesRefactorLoader",
    "FlextInfraUtilitiesRefactorMroScan",
    "FlextInfraUtilitiesRefactorMroTransform",
    "FlextInfraUtilitiesRefactorNamespace",
    "FlextInfraUtilitiesRefactorPydantic",
    "FlextInfraUtilitiesRefactorPydanticAnalysis",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesRope",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesSelection",
    "FlextInfraUtilitiesSubprocess",
    "FlextInfraUtilitiesTemplates",
    "FlextInfraUtilitiesTerminal",
    "FlextInfraUtilitiesToml",
    "FlextInfraUtilitiesTomlParse",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesYaml",
    "FlextInfraViolationCensusVisitor",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceConstants",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceMakefileGenerator",
    "FlextInfraWorkspaceMode",
    "FlextInfraWorkspaceModels",
    "__all__",
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
    "basemk",
    "build_parser",
    "c",
    "check",
    "codegen",
    "d",
    "deps",
    "detectors",
    "docs",
    "e",
    "gates",
    "h",
    "logger",
    "m",
    "main",
    "maintenance",
    "output",
    "p",
    "r",
    "refactor",
    "register_rope_hooks",
    "release",
    "rules",
    "run_cli",
    "run_mro_migration_hook",
    "s",
    "t",
    "transformers",
    "u",
    "validate",
    "workspace",
    "x",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
