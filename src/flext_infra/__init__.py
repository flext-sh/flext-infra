# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)
from flext_infra.__version__ import *

if _t.TYPE_CHECKING:
    from flext_cli import d, e, h, r, x
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
    from flext_infra._models.deps import FlextInfraModelsDeps
    from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolSettings
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
    from flext_infra._models.mixins import FlextInfraModelsMixins
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
    from flext_infra._protocols.check import FlextInfraProtocolsCheck
    from flext_infra._protocols.rope import FlextInfraProtocolsRope
    from flext_infra._typings.adapters import FlextInfraTypesAdapters
    from flext_infra._typings.base import FlextInfraTypesBase
    from flext_infra._typings.rope import FlextInfraTypesRope
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
    from flext_infra._utilities.deps_path_sync import (
        FlextInfraUtilitiesDependencyPathSync,
    )
    from flext_infra._utilities.deps_repos import FlextInfraInternalSyncRepoMixin
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
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
    from flext_infra._utilities.github import FlextInfraUtilitiesGithub
    from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.mro_scan import FlextInfraUtilitiesRefactorMroScan
    from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
    from flext_infra._utilities.namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceMro,
    )
    from flext_infra._utilities.namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
    )
    from flext_infra._utilities.namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades,
    )
    from flext_infra._utilities.namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
    from flext_infra._utilities.policy import FlextInfraUtilitiesRefactorPolicy
    from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
    from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease
    from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
    from flext_infra._utilities.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
    from flext_infra._utilities.rope_module_patch import (
        FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities.rope_mro_transform import (
        FlextInfraUtilitiesRopeMroTransform,
    )
    from flext_infra._utilities.rope_pep695_patch import (
        FlextInfraUtilitiesRopePep695Patch,
    )
    from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra.api import FlextInfra, infra
    from flext_infra.base import (
        FlextInfraProjectSelectionServiceBase,
        FlextInfraServiceBase,
        s,
    )
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
    from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
    from flext_infra.check.workspace_check_gates import (
        FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin,
    )
    from flext_infra.cli import FlextInfraCli, main
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
    from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
    from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.pyproject_keys import FlextInfraCodegenPyprojectKeys
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
    from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile
    from flext_infra.constants import FlextInfraConstants, c
    from flext_infra.deps.detection import FlextInfraDependencyDetectionService
    from flext_infra.deps.detection_analysis import (
        FlextInfraDependencyDetectionAnalysis,
    )
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
    from flext_infra.deps.detector_runtime import FlextInfraDependencyDetectorRuntime
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
    from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
    from flext_infra.deps.phase_engine import FlextInfraPhaseEngine
    from flext_infra.deps.phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps.phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps.phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps.phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
    from flext_infra.deps.phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps.phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
    from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector,
    )
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector,
    )
    from flext_infra.detectors.facade_scanner import FlextInfraScanner
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
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector,
    )
    from flext_infra.detectors.silent_failure_detector import (
        FlextInfraSilentFailureDetector,
    )
    from flext_infra.docs.auditor import FlextInfraDocAuditor
    from flext_infra.docs.auditor_mixin import FlextInfraDocAuditorMixin
    from flext_infra.docs.base import FlextInfraDocServiceBase
    from flext_infra.docs.builder import FlextInfraDocBuilder
    from flext_infra.docs.fixer import FlextInfraDocFixer
    from flext_infra.docs.generator import FlextInfraDocGenerator
    from flext_infra.docs.validator import FlextInfraDocValidator
    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.base_gate import FlextInfraGate
    from flext_infra.gates.go import FlextInfraGoGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
    from flext_infra.gates.silent_failure import FlextInfraSilentFailureGate
    from flext_infra.maintenance.python_version import FlextInfraPythonVersionEnforcer
    from flext_infra.models import FlextInfraModels, m
    from flext_infra.protocols import FlextInfraProtocols, p
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.engine import FlextInfraRefactorEngine
    from flext_infra.refactor.engine_file import (
        FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor,
    )
    from flext_infra.refactor.engine_legacy import FlextInfraRefactorLegacyTextOps
    from flext_infra.refactor.engine_text import FlextInfraRefactorTextExecutor
    from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader
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
    from flext_infra.refactor.namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin,
    )
    from flext_infra.refactor.orchestrator import FlextInfraRefactorOrchestrator
    from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
    from flext_infra.release.orchestrator_phases import (
        FlextInfraReleaseOrchestratorPhases,
    )
    from flext_infra.settings import FlextInfraSettings
    from flext_infra.transformers.base import (
        FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer,
    )
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
    from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor,
    )
    from flext_infra.typings import FlextInfraTypes, t
    from flext_infra.utilities import FlextInfraUtilities, u
    from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
    from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
    from flext_infra.validate.import_cycles import FlextInfraValidateImportCycles
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.lazy_map_freshness import (
        FlextInfraValidateLazyMapFreshness,
    )
    from flext_infra.validate.metadata_discipline import (
        FlextInfraValidateMetadataDiscipline,
    )
    from flext_infra.validate.namespace_rules import FlextInfraNamespaceRules
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
    from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist
    from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
    from flext_infra.workspace.rope import FlextInfraRopeWorkspace
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
        ".maintenance",
        ".refactor",
        ".release",
        ".transformers",
        ".validate",
        ".workspace",
    ),
    build_lazy_import_map(
        {
            ".__version__": (
                "__author__",
                "__author_email__",
                "__description__",
                "__license__",
                "__title__",
                "__url__",
                "__version__",
                "__version_info__",
            ),
            "._constants.base": ("FlextInfraConstantsBase",),
            "._constants.basemk": ("FlextInfraConstantsBasemk",),
            "._constants.census": ("FlextInfraConstantsCensus",),
            "._constants.check": ("FlextInfraConstantsCheck",),
            "._constants.codegen": ("FlextInfraConstantsCodegen",),
            "._constants.deps": ("FlextInfraConstantsDeps",),
            "._constants.docs": ("FlextInfraConstantsDocs",),
            "._constants.github": ("FlextInfraConstantsGithub",),
            "._constants.make": ("FlextInfraConstantsMake",),
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
            "._utilities.base": ("FlextInfraUtilitiesBase",),
            "._utilities.census": ("FlextInfraUtilitiesRefactorCensus",),
            "._utilities.codegen": ("FlextInfraUtilitiesCodegen",),
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
            "._utilities.github": ("FlextInfraUtilitiesGithub",),
            "._utilities.github_pr": ("FlextInfraUtilitiesGithubPr",),
            "._utilities.iteration": ("FlextInfraUtilitiesIteration",),
            "._utilities.log_parser": ("FlextInfraUtilitiesLogParser",),
            "._utilities.mro_scan": ("FlextInfraUtilitiesRefactorMroScan",),
            "._utilities.namespace": ("FlextInfraUtilitiesCodegenNamespace",),
            "._utilities.namespace_analysis": (
                "FlextInfraUtilitiesRefactorNamespaceMro",
            ),
            "._utilities.namespace_common": (
                "FlextInfraUtilitiesRefactorNamespaceCommon",
            ),
            "._utilities.namespace_facades": (
                "FlextInfraUtilitiesRefactorNamespaceFacades",
            ),
            "._utilities.namespace_moves": (
                "FlextInfraUtilitiesRefactorNamespaceMoves",
            ),
            "._utilities.patterns": ("FlextInfraUtilitiesPatterns",),
            "._utilities.policy": ("FlextInfraUtilitiesRefactorPolicy",),
            "._utilities.protected_edit": ("FlextInfraUtilitiesProtectedEdit",),
            "._utilities.refactor": ("FlextInfraUtilitiesRefactor",),
            "._utilities.release": ("FlextInfraUtilitiesRelease",),
            "._utilities.rope_analysis": ("FlextInfraUtilitiesRopeAnalysis",),
            "._utilities.rope_analysis_introspection": (
                "FlextInfraUtilitiesRopeAnalysisIntrospection",
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
            ".gates.bandit": ("FlextInfraBanditGate",),
            ".gates.base_gate": ("FlextInfraGate",),
            ".gates.go": ("FlextInfraGoGate",),
            ".gates.markdown": ("FlextInfraMarkdownGate",),
            ".gates.mypy": ("FlextInfraMypyGate",),
            ".gates.pyrefly": ("FlextInfraPyreflyGate",),
            ".gates.pyright": ("FlextInfraPyrightGate",),
            ".gates.ruff_format": ("FlextInfraRuffFormatGate",),
            ".gates.ruff_lint": ("FlextInfraRuffLintGate",),
            ".gates.silent_failure": ("FlextInfraSilentFailureGate",),
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
            ".transformers.mro_remover": ("FlextInfraRefactorMRORemover",),
            ".transformers.mro_symbol_propagator": (
                "FlextInfraRefactorMROSymbolPropagator",
            ),
            ".transformers.nested_class_propagation": (
                "FlextInfraNestedClassPropagationTransformer",
            ),
            ".transformers.signature_propagator": (
                "FlextInfraRefactorSignaturePropagator",
            ),
            ".transformers.symbol_propagator": ("FlextInfraRefactorSymbolPropagator",),
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
            ".validate.import_cycles": ("FlextInfraValidateImportCycles",),
            ".validate.inventory": ("FlextInfraInventoryService",),
            ".validate.lazy_map_freshness": ("FlextInfraValidateLazyMapFreshness",),
            ".validate.metadata_discipline": ("FlextInfraValidateMetadataDiscipline",),
            ".validate.namespace_rules": ("FlextInfraNamespaceRules",),
            ".validate.namespace_validator": ("FlextInfraNamespaceValidator",),
            ".validate.pytest_diag": ("FlextInfraPytestDiagExtractor",),
            ".validate.scanner": ("FlextInfraTextPatternScanner",),
            ".validate.silent_failure": ("FlextInfraSilentFailureValidator",),
            ".validate.skill_validator": ("FlextInfraSkillValidator",),
            ".validate.stub_chain": ("FlextInfraStubSupplyChain",),
            ".validate.tier_whitelist": ("FlextInfraValidateTierWhitelist",),
            ".workspace.detector": ("FlextInfraWorkspaceDetector",),
            ".workspace.migrator": ("FlextInfraProjectMigrator",),
            ".workspace.orchestrator": ("FlextInfraOrchestratorService",),
            ".workspace.project_makefile": ("FlextInfraProjectMakefileUpdater",),
            ".workspace.rope": ("FlextInfraRopeWorkspace",),
            ".workspace.sync": ("FlextInfraSyncService",),
            ".workspace.workspace_makefile": ("FlextInfraWorkspaceMakefileGenerator",),
            "flext_cli": (
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)

__all__: list[str] = [
    "FlextInfra",
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
    "FlextInfraConstantsBase",
    "FlextInfraConstantsBasemk",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCheck",
    "FlextInfraConstantsCodegen",
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
    "FlextInfraGateRegistry",
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
    "FlextInfraModelsCore",
    "FlextInfraModelsDeps",
    "FlextInfraModelsDepsToolConfigLinters",
    "FlextInfraModelsDepsToolConfigTypeCheckers",
    "FlextInfraModelsDepsToolSettings",
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
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsCheck",
    "FlextInfraProtocolsRope",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorFileExecutor",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorLegacyTextOps",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorOrchestrator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
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
    "FlextInfraTypesAdapters",
    "FlextInfraTypesBase",
    "FlextInfraTypesRope",
    "FlextInfraUtilities",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesDependencyPathSync",
    "FlextInfraUtilitiesDiscovery",
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
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesGithubPr",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorEngine",
    "FlextInfraUtilitiesRefactorMroScan",
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceFacades",
    "FlextInfraUtilitiesRefactorNamespaceMoves",
    "FlextInfraUtilitiesRefactorNamespaceMro",
    "FlextInfraUtilitiesRefactorPolicy",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeInventory",
    "FlextInfraUtilitiesRopeModulePatch",
    "FlextInfraUtilitiesRopeMroTransform",
    "FlextInfraUtilitiesRopePep695Patch",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraValidateFreshImport",
    "FlextInfraValidateImportCycles",
    "FlextInfraValidateLazyMapFreshness",
    "FlextInfraValidateMetadataDiscipline",
    "FlextInfraValidateTierWhitelist",
    "FlextInfraViolationCensusVisitor",
    "FlextInfraWorkspaceCheckGatesMixin",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceMakefileGenerator",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
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
]
