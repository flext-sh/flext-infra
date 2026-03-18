# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Public API for flext-infra.

Provides access to infrastructure services for workspace management, validation,
dependency handling, and build orchestration in the FLEXT ecosystem.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from flext_infra import (
        _utilities,
        basemk,
        check,
        codegen,
        deps,
        docs,
        gates,
        github,
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
    from flext_infra._utilities.cli import FlextInfraUtilitiesCli
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
    from flext_infra._utilities.git import FlextInfraUtilitiesGit
    from flext_infra._utilities.io import FlextInfraUtilitiesIo
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.output import (
        FlextInfraUtilitiesOutput,
        OutputBackend,
        output,
    )
    from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
    from flext_infra._utilities.paths import FlextInfraUtilitiesPaths
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
    from flext_infra._utilities.reporting import FlextInfraUtilitiesReporting
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
    from flext_infra._utilities.scanning import FlextInfraUtilitiesScanning
    from flext_infra._utilities.selection import FlextInfraUtilitiesSelection
    from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess
    from flext_infra._utilities.templates import FlextInfraUtilitiesTemplates
    from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
    from flext_infra._utilities.toml import FlextInfraUtilitiesToml
    from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
    from flext_infra.check.services import (
        CheckIssue,
        FlextInfraConfigFixer,
        GateExecution,
        ProjectResult,
        ProjectResult as r,
    )
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker,
        build_parser,
        run_cli,
    )
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenConstantsQualityGate,
    )
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
    from flext_infra.codegen.transforms import FlextInfraCodegenTransforms
    from flext_infra.constants import FlextInfraConstants, c
    from flext_infra.deps._phases.consolidate_groups import ConsolidateGroupsPhase
    from flext_infra.deps._phases.ensure_coverage import EnsureCoverageConfigPhase
    from flext_infra.deps._phases.ensure_extra_paths import EnsureExtraPathsPhase
    from flext_infra.deps._phases.ensure_formatting import EnsureFormattingToolingPhase
    from flext_infra.deps._phases.ensure_mypy import EnsureMypyConfigPhase
    from flext_infra.deps._phases.ensure_namespace import EnsureNamespaceToolingPhase
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        EnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import EnsurePyreflyConfigPhase
    from flext_infra.deps._phases.ensure_pyright import EnsurePyrightConfigPhase
    from flext_infra.deps._phases.ensure_pytest import EnsurePytestConfigPhase
    from flext_infra.deps._phases.ensure_ruff import EnsureRuffConfigPhase
    from flext_infra.deps._phases.inject_comments import InjectCommentsPhase
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionHelpers,
        FlextInfraDependencyDetectionService,
        FlextInfraDependencyDetectionService as s,
        dm,
    )
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService,
        shutil,
    )
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
    from flext_infra.deps.path_sync import FlextInfraDependencyPathSync
    from flext_infra.deps.tool_config import FlextInfraDependencyToolConfig
    from flext_infra.docs.auditor import FlextInfraDocAuditor
    from flext_infra.docs.builder import FlextInfraDocBuilder
    from flext_infra.docs.fixer import FlextInfraDocFixer
    from flext_infra.docs.generator import FlextInfraDocGenerator
    from flext_infra.docs.shared import FlextInfraDocsShared
    from flext_infra.docs.validator import FlextInfraDocValidator
    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.go import FlextInfraGoGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
    from flext_infra.github.linter import FlextInfraWorkflowLinter
    from flext_infra.github.pr import FlextInfraPrManager
    from flext_infra.github.pr_workspace import FlextInfraPrWorkspaceManager
    from flext_infra.github.workflows import FlextInfraWorkflowSyncer, SyncOperation
    from flext_infra.models import FlextInfraModels, m
    from flext_infra.protocols import FlextInfraProtocols, p
    from flext_infra.refactor._detectors.import_collector import ImportCollector
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.dependency_analyzer import (
        ClassPlacementDetector,
        CompatibilityAliasDetector,
        CyclicImportDetector,
        DependencyAnalyzer,
        FlextInfraRefactorDependencyAnalyzerFacade,
        FutureAnnotationsDetector,
        ImportAliasDetector,
        InternalImportDetector,
        LooseObjectDetector,
        ManualProtocolDetector,
        ManualTypingAliasDetector,
        MROCompletenessDetector,
        NamespaceFacadeScanner,
        NamespaceSourceDetector,
        RuntimeAliasDetector,
    )
    from flext_infra.refactor.engine import FlextInfraRefactorEngine
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.mro_migrator import (
        FlextInfraRefactorMROMigrationTransformer,
    )
    from flext_infra.refactor.mro_resolver import (
        FlextInfraRefactorMROImportRewriter,
        FlextInfraRefactorMROMigrationScanner,
        FlextInfraRefactorMROResolver,
    )
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
    from flext_infra.refactor.namespace_rewriter import NamespaceEnforcementRewriter
    from flext_infra.refactor.output import FlextInfraRefactorOutputRenderer
    from flext_infra.refactor.project_classifier import ProjectClassifier
    from flext_infra.refactor.pydantic_centralizer import (
        FlextInfraRefactorPydanticCentralizer,
    )
    from flext_infra.refactor.pydantic_centralizer_analysis import (
        FlextInfraRefactorPydanticCentralizerAnalysis,
    )
    from flext_infra.refactor.rule import (
        FlextInfraRefactorRule,
        FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.validation import (
        FlextInfraRefactorCliSupport,
        FlextInfraRefactorMROMigrationValidator,
        FlextInfraRefactorRuleDefinitionValidator,
        PostCheckGate,
    )
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
    from flext_infra.rules.class_nesting import ClassNestingRefactorRule
    from flext_infra.rules.class_reconstructor import (
        FlextInfraRefactorClassNestingReconstructor,
        FlextInfraRefactorClassReconstructorRule,
        PreCheckGate,
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
    from flext_infra.transformers.alias_remover import FlextInfraRefactorAliasRemover
    from flext_infra.transformers.census_visitors import (
        CensusImportDiscoveryVisitor,
        CensusUsageCollector,
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
        HelperConsolidationTransformer,
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
    from flext_infra.transformers.mro_reference_rewriter import (
        FlextInfraRefactorMROReferenceRewriter,
    )
    from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
    from flext_infra.transformers.nested_class_propagation import (
        NestedClassPropagationTransformer,
    )
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.typings import FlextInfraTypes, t
    from flext_infra.utilities import FlextInfraUtilities, u
    from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
    from flext_infra.workspace import maintenance
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector,
        WorkspaceMode,
    )
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer,
        logger,
    )
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.sync import FlextInfraSyncService

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "CensusImportDiscoveryVisitor": (
        "flext_infra.transformers.census_visitors",
        "CensusImportDiscoveryVisitor",
    ),
    "CensusUsageCollector": (
        "flext_infra.transformers.census_visitors",
        "CensusUsageCollector",
    ),
    "CheckIssue": ("flext_infra.check.services", "CheckIssue"),
    "ClassNestingRefactorRule": (
        "flext_infra.rules.class_nesting",
        "ClassNestingRefactorRule",
    ),
    "ClassPlacementDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ClassPlacementDetector",
    ),
    "CompatibilityAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "CompatibilityAliasDetector",
    ),
    "ConsolidateGroupsPhase": (
        "flext_infra.deps._phases.consolidate_groups",
        "ConsolidateGroupsPhase",
    ),
    "CyclicImportDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "CyclicImportDetector",
    ),
    "DependencyAnalyzer": (
        "flext_infra.refactor.dependency_analyzer",
        "DependencyAnalyzer",
    ),
    "EnsureCoverageConfigPhase": (
        "flext_infra.deps._phases.ensure_coverage",
        "EnsureCoverageConfigPhase",
    ),
    "EnsureExtraPathsPhase": (
        "flext_infra.deps._phases.ensure_extra_paths",
        "EnsureExtraPathsPhase",
    ),
    "EnsureFormattingToolingPhase": (
        "flext_infra.deps._phases.ensure_formatting",
        "EnsureFormattingToolingPhase",
    ),
    "EnsureMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_mypy",
        "EnsureMypyConfigPhase",
    ),
    "EnsureNamespaceToolingPhase": (
        "flext_infra.deps._phases.ensure_namespace",
        "EnsureNamespaceToolingPhase",
    ),
    "EnsurePydanticMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "EnsurePydanticMypyConfigPhase",
    ),
    "EnsurePyreflyConfigPhase": (
        "flext_infra.deps._phases.ensure_pyrefly",
        "EnsurePyreflyConfigPhase",
    ),
    "EnsurePyrightConfigPhase": (
        "flext_infra.deps._phases.ensure_pyright",
        "EnsurePyrightConfigPhase",
    ),
    "EnsurePytestConfigPhase": (
        "flext_infra.deps._phases.ensure_pytest",
        "EnsurePytestConfigPhase",
    ),
    "EnsureRuffConfigPhase": (
        "flext_infra.deps._phases.ensure_ruff",
        "EnsureRuffConfigPhase",
    ),
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
    "FlextInfraCodegenCensus": (
        "flext_infra.codegen.census",
        "FlextInfraCodegenCensus",
    ),
    "FlextInfraCodegenConstantsQualityGate": (
        "flext_infra.codegen.constants_quality_gate",
        "FlextInfraCodegenConstantsQualityGate",
    ),
    "FlextInfraCodegenFixer": ("flext_infra.codegen.fixer", "FlextInfraCodegenFixer"),
    "FlextInfraCodegenLazyInit": (
        "flext_infra.codegen.lazy_init",
        "FlextInfraCodegenLazyInit",
    ),
    "FlextInfraCodegenPyTyped": (
        "flext_infra.codegen.py_typed",
        "FlextInfraCodegenPyTyped",
    ),
    "FlextInfraCodegenScaffolder": (
        "flext_infra.codegen.scaffolder",
        "FlextInfraCodegenScaffolder",
    ),
    "FlextInfraCodegenTransforms": (
        "flext_infra.codegen.transforms",
        "FlextInfraCodegenTransforms",
    ),
    "FlextInfraConfigFixer": ("flext_infra.check.services", "FlextInfraConfigFixer"),
    "FlextInfraConstants": ("flext_infra.constants", "FlextInfraConstants"),
    "FlextInfraDependencyDetectionHelpers": (
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionHelpers",
    ),
    "FlextInfraDependencyDetectionService": (
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionService",
    ),
    "FlextInfraDependencyPathSync": (
        "flext_infra.deps.path_sync",
        "FlextInfraDependencyPathSync",
    ),
    "FlextInfraDependencyToolConfig": (
        "flext_infra.deps.tool_config",
        "FlextInfraDependencyToolConfig",
    ),
    "FlextInfraDocAuditor": ("flext_infra.docs.auditor", "FlextInfraDocAuditor"),
    "FlextInfraDocBuilder": ("flext_infra.docs.builder", "FlextInfraDocBuilder"),
    "FlextInfraDocFixer": ("flext_infra.docs.fixer", "FlextInfraDocFixer"),
    "FlextInfraDocGenerator": ("flext_infra.docs.generator", "FlextInfraDocGenerator"),
    "FlextInfraDocValidator": ("flext_infra.docs.validator", "FlextInfraDocValidator"),
    "FlextInfraDocsShared": ("flext_infra.docs.shared", "FlextInfraDocsShared"),
    "FlextInfraExtraPathsManager": (
        "flext_infra.deps.extra_paths",
        "FlextInfraExtraPathsManager",
    ),
    "FlextInfraGoGate": ("flext_infra.gates.go", "FlextInfraGoGate"),
    "FlextInfraInternalDependencySyncService": (
        "flext_infra.deps.internal_sync",
        "FlextInfraInternalDependencySyncService",
    ),
    "FlextInfraInventoryService": (
        "flext_infra.validate.inventory",
        "FlextInfraInventoryService",
    ),
    "FlextInfraMarkdownGate": ("flext_infra.gates.markdown", "FlextInfraMarkdownGate"),
    "FlextInfraModels": ("flext_infra.models", "FlextInfraModels"),
    "FlextInfraMypyGate": ("flext_infra.gates.mypy", "FlextInfraMypyGate"),
    "FlextInfraNamespaceEnforcer": (
        "flext_infra.refactor.namespace_enforcer",
        "FlextInfraNamespaceEnforcer",
    ),
    "FlextInfraNamespaceValidator": (
        "flext_infra.validate.namespace_validator",
        "FlextInfraNamespaceValidator",
    ),
    "FlextInfraOrchestratorService": (
        "flext_infra.workspace.orchestrator",
        "FlextInfraOrchestratorService",
    ),
    "FlextInfraPrManager": ("flext_infra.github.pr", "FlextInfraPrManager"),
    "FlextInfraPrWorkspaceManager": (
        "flext_infra.github.pr_workspace",
        "FlextInfraPrWorkspaceManager",
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
    "FlextInfraRefactorClassNestingReconstructor": (
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassNestingReconstructor",
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
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassReconstructorRule",
    ),
    "FlextInfraRefactorCliSupport": (
        "flext_infra.refactor.validation",
        "FlextInfraRefactorCliSupport",
    ),
    "FlextInfraRefactorDependencyAnalyzerFacade": (
        "flext_infra.refactor.dependency_analyzer",
        "FlextInfraRefactorDependencyAnalyzerFacade",
    ),
    "FlextInfraRefactorDeprecatedRemover": (
        "flext_infra.transformers.deprecated_remover",
        "FlextInfraRefactorDeprecatedRemover",
    ),
    "FlextInfraRefactorEngine": (
        "flext_infra.refactor.engine",
        "FlextInfraRefactorEngine",
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
    "FlextInfraRefactorLooseClassScanner": (
        "flext_infra.refactor.scanner",
        "FlextInfraRefactorLooseClassScanner",
    ),
    "FlextInfraRefactorMROClassMigrationRule": (
        "flext_infra.rules.mro_class_migration",
        "FlextInfraRefactorMROClassMigrationRule",
    ),
    "FlextInfraRefactorMROImportRewriter": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROImportRewriter",
    ),
    "FlextInfraRefactorMROMigrationScanner": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROMigrationScanner",
    ),
    "FlextInfraRefactorMROMigrationTransformer": (
        "flext_infra.refactor.mro_migrator",
        "FlextInfraRefactorMROMigrationTransformer",
    ),
    "FlextInfraRefactorMROMigrationValidator": (
        "flext_infra.refactor.validation",
        "FlextInfraRefactorMROMigrationValidator",
    ),
    "FlextInfraRefactorMROPrivateInlineTransformer": (
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROPrivateInlineTransformer",
    ),
    "FlextInfraRefactorMROQualifiedReferenceTransformer": (
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROQualifiedReferenceTransformer",
    ),
    "FlextInfraRefactorMRORedundancyChecker": (
        "flext_infra.rules.mro_redundancy_checker",
        "FlextInfraRefactorMRORedundancyChecker",
    ),
    "FlextInfraRefactorMROReferenceRewriter": (
        "flext_infra.transformers.mro_reference_rewriter",
        "FlextInfraRefactorMROReferenceRewriter",
    ),
    "FlextInfraRefactorMRORemover": (
        "flext_infra.transformers.mro_remover",
        "FlextInfraRefactorMRORemover",
    ),
    "FlextInfraRefactorMROResolver": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROResolver",
    ),
    "FlextInfraRefactorMigrateToClassMRO": (
        "flext_infra.refactor.migrate_to_class_mro",
        "FlextInfraRefactorMigrateToClassMRO",
    ),
    "FlextInfraRefactorOutputRenderer": (
        "flext_infra.refactor.output",
        "FlextInfraRefactorOutputRenderer",
    ),
    "FlextInfraRefactorPatternCorrectionsRule": (
        "flext_infra.rules.pattern_corrections",
        "FlextInfraRefactorPatternCorrectionsRule",
    ),
    "FlextInfraRefactorPydanticCentralizer": (
        "flext_infra.refactor.pydantic_centralizer",
        "FlextInfraRefactorPydanticCentralizer",
    ),
    "FlextInfraRefactorPydanticCentralizerAnalysis": (
        "flext_infra.refactor.pydantic_centralizer_analysis",
        "FlextInfraRefactorPydanticCentralizerAnalysis",
    ),
    "FlextInfraRefactorRule": ("flext_infra.refactor.rule", "FlextInfraRefactorRule"),
    "FlextInfraRefactorRuleDefinitionValidator": (
        "flext_infra.refactor.validation",
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
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSignaturePropagationRule",
    ),
    "FlextInfraRefactorSignaturePropagator": (
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSignaturePropagator",
    ),
    "FlextInfraRefactorSymbolPropagationRule": (
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSymbolPropagationRule",
    ),
    "FlextInfraRefactorSymbolPropagator": (
        "flext_infra.transformers.symbol_propagator",
        "FlextInfraRefactorSymbolPropagator",
    ),
    "FlextInfraRefactorTransformerPolicyUtilities": (
        "flext_infra.transformers.policy",
        "FlextInfraRefactorTransformerPolicyUtilities",
    ),
    "FlextInfraRefactorViolationAnalyzer": (
        "flext_infra.refactor.violation_analyzer",
        "FlextInfraRefactorViolationAnalyzer",
    ),
    "FlextInfraReleaseOrchestrator": (
        "flext_infra.release.orchestrator",
        "FlextInfraReleaseOrchestrator",
    ),
    "FlextInfraRuffFormatGate": (
        "flext_infra.gates.ruff_format",
        "FlextInfraRuffFormatGate",
    ),
    "FlextInfraRuffLintGate": ("flext_infra.gates.ruff_lint", "FlextInfraRuffLintGate"),
    "FlextInfraRuntimeDevDependencyDetector": (
        "flext_infra.deps.detector",
        "FlextInfraRuntimeDevDependencyDetector",
    ),
    "FlextInfraSkillValidator": (
        "flext_infra.validate.skill_validator",
        "FlextInfraSkillValidator",
    ),
    "FlextInfraStubSupplyChain": (
        "flext_infra.validate.stub_chain",
        "FlextInfraStubSupplyChain",
    ),
    "FlextInfraSyncService": ("flext_infra.workspace.sync", "FlextInfraSyncService"),
    "FlextInfraTextPatternScanner": (
        "flext_infra.validate.scanner",
        "FlextInfraTextPatternScanner",
    ),
    "FlextInfraTypes": ("flext_infra.typings", "FlextInfraTypes"),
    "FlextInfraUtilities": ("flext_infra.utilities", "FlextInfraUtilities"),
    "FlextInfraUtilitiesCli": ("flext_infra._utilities.cli", "FlextInfraUtilitiesCli"),
    "FlextInfraUtilitiesDiscovery": (
        "flext_infra._utilities.discovery",
        "FlextInfraUtilitiesDiscovery",
    ),
    "FlextInfraUtilitiesFormatting": (
        "flext_infra._utilities.formatting",
        "FlextInfraUtilitiesFormatting",
    ),
    "FlextInfraUtilitiesGit": ("flext_infra._utilities.git", "FlextInfraUtilitiesGit"),
    "FlextInfraUtilitiesIo": ("flext_infra._utilities.io", "FlextInfraUtilitiesIo"),
    "FlextInfraUtilitiesIteration": (
        "flext_infra._utilities.iteration",
        "FlextInfraUtilitiesIteration",
    ),
    "FlextInfraUtilitiesOutput": (
        "flext_infra._utilities.output",
        "FlextInfraUtilitiesOutput",
    ),
    "FlextInfraUtilitiesParsing": (
        "flext_infra._utilities.parsing",
        "FlextInfraUtilitiesParsing",
    ),
    "FlextInfraUtilitiesPaths": (
        "flext_infra._utilities.paths",
        "FlextInfraUtilitiesPaths",
    ),
    "FlextInfraUtilitiesPatterns": (
        "flext_infra._utilities.patterns",
        "FlextInfraUtilitiesPatterns",
    ),
    "FlextInfraUtilitiesReporting": (
        "flext_infra._utilities.reporting",
        "FlextInfraUtilitiesReporting",
    ),
    "FlextInfraUtilitiesSafety": (
        "flext_infra._utilities.safety",
        "FlextInfraUtilitiesSafety",
    ),
    "FlextInfraUtilitiesScanning": (
        "flext_infra._utilities.scanning",
        "FlextInfraUtilitiesScanning",
    ),
    "FlextInfraUtilitiesSelection": (
        "flext_infra._utilities.selection",
        "FlextInfraUtilitiesSelection",
    ),
    "FlextInfraUtilitiesSubprocess": (
        "flext_infra._utilities.subprocess",
        "FlextInfraUtilitiesSubprocess",
    ),
    "FlextInfraUtilitiesTemplates": (
        "flext_infra._utilities.templates",
        "FlextInfraUtilitiesTemplates",
    ),
    "FlextInfraUtilitiesTerminal": (
        "flext_infra._utilities.terminal",
        "FlextInfraUtilitiesTerminal",
    ),
    "FlextInfraUtilitiesToml": (
        "flext_infra._utilities.toml",
        "FlextInfraUtilitiesToml",
    ),
    "FlextInfraUtilitiesTomlParse": (
        "flext_infra._utilities.toml_parse",
        "FlextInfraUtilitiesTomlParse",
    ),
    "FlextInfraUtilitiesVersioning": (
        "flext_infra._utilities.versioning",
        "FlextInfraUtilitiesVersioning",
    ),
    "FlextInfraUtilitiesYaml": (
        "flext_infra._utilities.yaml",
        "FlextInfraUtilitiesYaml",
    ),
    "FlextInfraWorkflowLinter": (
        "flext_infra.github.linter",
        "FlextInfraWorkflowLinter",
    ),
    "FlextInfraWorkflowSyncer": (
        "flext_infra.github.workflows",
        "FlextInfraWorkflowSyncer",
    ),
    "FlextInfraWorkspaceChecker": (
        "flext_infra.check.workspace_check",
        "FlextInfraWorkspaceChecker",
    ),
    "FlextInfraWorkspaceDetector": (
        "flext_infra.workspace.detector",
        "FlextInfraWorkspaceDetector",
    ),
    "FutureAnnotationsDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "FutureAnnotationsDetector",
    ),
    "GateExecution": ("flext_infra.check.services", "GateExecution"),
    "HelperConsolidationTransformer": (
        "flext_infra.transformers.helper_consolidation",
        "HelperConsolidationTransformer",
    ),
    "ImportAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ImportAliasDetector",
    ),
    "ImportCollector": (
        "flext_infra.refactor._detectors.import_collector",
        "ImportCollector",
    ),
    "InjectCommentsPhase": (
        "flext_infra.deps._phases.inject_comments",
        "InjectCommentsPhase",
    ),
    "InternalImportDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "InternalImportDetector",
    ),
    "LooseObjectDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "LooseObjectDetector",
    ),
    "MROCompletenessDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "MROCompletenessDetector",
    ),
    "ManualProtocolDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ManualProtocolDetector",
    ),
    "ManualTypingAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ManualTypingAliasDetector",
    ),
    "NamespaceEnforcementRewriter": (
        "flext_infra.refactor.namespace_rewriter",
        "NamespaceEnforcementRewriter",
    ),
    "NamespaceFacadeScanner": (
        "flext_infra.refactor.dependency_analyzer",
        "NamespaceFacadeScanner",
    ),
    "NamespaceSourceDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "NamespaceSourceDetector",
    ),
    "NestedClassPropagationTransformer": (
        "flext_infra.transformers.nested_class_propagation",
        "NestedClassPropagationTransformer",
    ),
    "OutputBackend": ("flext_infra._utilities.output", "OutputBackend"),
    "PostCheckGate": ("flext_infra.refactor.validation", "PostCheckGate"),
    "PreCheckGate": ("flext_infra.rules.class_reconstructor", "PreCheckGate"),
    "ProjectClassifier": (
        "flext_infra.refactor.project_classifier",
        "ProjectClassifier",
    ),
    "ProjectResult": ("flext_infra.check.services", "ProjectResult"),
    "RuntimeAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "RuntimeAliasDetector",
    ),
    "SyncOperation": ("flext_infra.github.workflows", "SyncOperation"),
    "WorkspaceMode": ("flext_infra.workspace.detector", "WorkspaceMode"),
    "__all__": ("flext_infra.__version__", "__all__"),
    "__author__": ("flext_infra.__version__", "__author__"),
    "__author_email__": ("flext_infra.__version__", "__author_email__"),
    "__description__": ("flext_infra.__version__", "__description__"),
    "__license__": ("flext_infra.__version__", "__license__"),
    "__title__": ("flext_infra.__version__", "__title__"),
    "__url__": ("flext_infra.__version__", "__url__"),
    "__version__": ("flext_infra.__version__", "__version__"),
    "__version_info__": ("flext_infra.__version__", "__version_info__"),
    "_utilities": ("flext_infra._utilities", ""),
    "basemk": ("flext_infra.basemk", ""),
    "build_parser": ("flext_infra.check.workspace_check", "build_parser"),
    "c": ("flext_infra.constants", "c"),
    "check": ("flext_infra.check", ""),
    "codegen": ("flext_infra.codegen", ""),
    "deps": ("flext_infra.deps", ""),
    "dm": ("flext_infra.deps.detection", "dm"),
    "docs": ("flext_infra.docs", ""),
    "gates": ("flext_infra.gates", ""),
    "github": ("flext_infra.github", ""),
    "logger": ("flext_infra.workspace.maintenance.python_version", "logger"),
    "m": ("flext_infra.models", "m"),
    "maintenance": ("flext_infra.workspace.maintenance", ""),
    "output": ("flext_infra._utilities.output", "output"),
    "p": ("flext_infra.protocols", "p"),
    "r": ("flext_infra.check.services", "ProjectResult"),
    "refactor": ("flext_infra.refactor", ""),
    "release": ("flext_infra.release", ""),
    "rules": ("flext_infra.rules", ""),
    "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
    "s": ("flext_infra.deps.detection", "FlextInfraDependencyDetectionService"),
    "shutil": ("flext_infra.deps.internal_sync", "shutil"),
    "t": ("flext_infra.typings", "t"),
    "transformers": ("flext_infra.transformers", ""),
    "u": ("flext_infra.utilities", "u"),
    "validate": ("flext_infra.validate", ""),
    "workspace": ("flext_infra.workspace", ""),
}

__all__ = [
    "CensusImportDiscoveryVisitor",
    "CensusUsageCollector",
    "CheckIssue",
    "ClassNestingRefactorRule",
    "ClassPlacementDetector",
    "CompatibilityAliasDetector",
    "ConsolidateGroupsPhase",
    "CyclicImportDetector",
    "DependencyAnalyzer",
    "EnsureCoverageConfigPhase",
    "EnsureExtraPathsPhase",
    "EnsureFormattingToolingPhase",
    "EnsureMypyConfigPhase",
    "EnsureNamespaceToolingPhase",
    "EnsurePydanticMypyConfigPhase",
    "EnsurePyreflyConfigPhase",
    "EnsurePyrightConfigPhase",
    "EnsurePytestConfigPhase",
    "EnsureRuffConfigPhase",
    "FlextInfraBanditGate",
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
    "FlextInfraBaseMkValidator",
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConstantsQualityGate",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenTransforms",
    "FlextInfraConfigFixer",
    "FlextInfraConstants",
    "FlextInfraDependencyDetectionHelpers",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyPathSync",
    "FlextInfraDependencyToolConfig",
    "FlextInfraDocAuditor",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
    "FlextInfraDocsShared",
    "FlextInfraExtraPathsManager",
    "FlextInfraGoGate",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraInventoryService",
    "FlextInfraMarkdownGate",
    "FlextInfraModels",
    "FlextInfraMypyGate",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceValidator",
    "FlextInfraOrchestratorService",
    "FlextInfraPrManager",
    "FlextInfraPrWorkspaceManager",
    "FlextInfraProjectMigrator",
    "FlextInfraProtocols",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassNestingReconstructor",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorCliSupport",
    "FlextInfraRefactorDependencyAnalyzerFacade",
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
    "FlextInfraRefactorMROMigrationScanner",
    "FlextInfraRefactorMROMigrationTransformer",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMROPrivateInlineTransformer",
    "FlextInfraRefactorMROQualifiedReferenceTransformer",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorMROReferenceRewriter",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorOutputRenderer",
    "FlextInfraRefactorPatternCorrectionsRule",
    "FlextInfraRefactorPydanticCentralizer",
    "FlextInfraRefactorPydanticCentralizerAnalysis",
    "FlextInfraRefactorRule",
    "FlextInfraRefactorRuleDefinitionValidator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTransformerPolicyUtilities",
    "FlextInfraRefactorViolationAnalyzer",
    "FlextInfraReleaseOrchestrator",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraSyncService",
    "FlextInfraTextPatternScanner",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "FlextInfraUtilitiesCli",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesIo",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesScanning",
    "FlextInfraUtilitiesSelection",
    "FlextInfraUtilitiesSubprocess",
    "FlextInfraUtilitiesTemplates",
    "FlextInfraUtilitiesTerminal",
    "FlextInfraUtilitiesToml",
    "FlextInfraUtilitiesTomlParse",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesYaml",
    "FlextInfraWorkflowLinter",
    "FlextInfraWorkflowSyncer",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceDetector",
    "FutureAnnotationsDetector",
    "GateExecution",
    "HelperConsolidationTransformer",
    "ImportAliasDetector",
    "ImportCollector",
    "InjectCommentsPhase",
    "InternalImportDetector",
    "LooseObjectDetector",
    "MROCompletenessDetector",
    "ManualProtocolDetector",
    "ManualTypingAliasDetector",
    "NamespaceEnforcementRewriter",
    "NamespaceFacadeScanner",
    "NamespaceSourceDetector",
    "NestedClassPropagationTransformer",
    "OutputBackend",
    "PostCheckGate",
    "PreCheckGate",
    "ProjectClassifier",
    "ProjectResult",
    "RuntimeAliasDetector",
    "SyncOperation",
    "WorkspaceMode",
    "__all__",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "_utilities",
    "basemk",
    "build_parser",
    "c",
    "check",
    "codegen",
    "deps",
    "dm",
    "docs",
    "gates",
    "github",
    "logger",
    "m",
    "maintenance",
    "output",
    "p",
    "r",
    "refactor",
    "release",
    "rules",
    "run_cli",
    "s",
    "shutil",
    "t",
    "transformers",
    "u",
    "validate",
    "workspace",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
