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

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

from flext_infra.__version__ import (
    FlextInfraVersion as FlextInfraVersion,
    __author__ as __author__,
    __author_email__ as __author_email__,
    __description__ as __description__,
    __license__ as __license__,
    __title__ as __title__,
    __url__ as __url__,
    __version__ as __version__,
    __version_info__ as __version_info__,
)

if TYPE_CHECKING:
    from flext_infra import (
        _constants as _constants,
        _models as _models,
        _protocols as _protocols,
        _typings as _typings,
        _utilities as _utilities,
        basemk as basemk,
        check as check,
        cli as cli,
        codegen as codegen,
        constants as constants,
        deps as deps,
        detectors as detectors,
        gates as gates,
        models as models,
        protocols as protocols,
        refactor as refactor,
        rules as rules,
        transformers as transformers,
        typings as typings,
        utilities as utilities,
        validate as validate,
        workspace as workspace,
    )
    from flext_infra._constants import (
        base as base,
        census as census,
        cst as cst,
        rope as rope,
    )
    from flext_infra._constants.base import (
        FlextInfraConstantsBase as FlextInfraConstantsBase,
    )
    from flext_infra._constants.census import (
        FlextInfraConstantsCensus as FlextInfraConstantsCensus,
    )
    from flext_infra._constants.cst import (
        FlextInfraConstantsCst as FlextInfraConstantsCst,
    )
    from flext_infra._constants.rope import (
        FlextInfraConstantsRope as FlextInfraConstantsRope,
    )
    from flext_infra._models import cli_inputs as cli_inputs, scan as scan
    from flext_infra._models.base import FlextInfraModelsBase as FlextInfraModelsBase
    from flext_infra._models.census import (
        FlextInfraModelsCensus as FlextInfraModelsCensus,
    )
    from flext_infra._models.cli_inputs import (
        FlextInfraModelsCliInputs as FlextInfraModelsCliInputs,
    )
    from flext_infra._models.cst import FlextInfraModelsCst as FlextInfraModelsCst
    from flext_infra._models.rope import FlextInfraModelsRope as FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan as FlextInfraModelsScan
    from flext_infra._protocols.base import (
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
    )
    from flext_infra._protocols.cst import (
        FlextInfraProtocolsCst as FlextInfraProtocolsCst,
    )
    from flext_infra._protocols.rope import (
        FlextInfraProtocolsRope as FlextInfraProtocolsRope,
    )
    from flext_infra._typings.base import FlextInfraTypesBase as FlextInfraTypesBase
    from flext_infra._typings.cst import FlextInfraTypesCst as FlextInfraTypesCst
    from flext_infra._typings.rope import FlextInfraTypesRope as FlextInfraTypesRope
    from flext_infra._utilities import (
        discovery as discovery,
        docs as docs,
        formatting as formatting,
        git as git,
        github as github,
        io as io,
        iteration as iteration,
        log_parser as log_parser,
        parsing as parsing,
        paths as paths,
        patterns as patterns,
        release as release,
        reporting as reporting,
        safety as safety,
        selection as selection,
        subprocess as subprocess,
        templates as templates,
        terminal as terminal,
        toml as toml,
        toml_parse as toml_parse,
        versioning as versioning,
        yaml as yaml,
    )
    from flext_infra._utilities.base import (
        FlextInfraUtilitiesBase as FlextInfraUtilitiesBase,
    )
    from flext_infra._utilities.cli import (
        FlextInfraUtilitiesCli as FlextInfraUtilitiesCli,
    )
    from flext_infra._utilities.cst import (
        FlextInfraUtilitiesCst as FlextInfraUtilitiesCst,
    )
    from flext_infra._utilities.discovery import (
        FlextInfraUtilitiesDiscovery as FlextInfraUtilitiesDiscovery,
    )
    from flext_infra._utilities.docs import (
        FlextInfraUtilitiesDocs as FlextInfraUtilitiesDocs,
    )
    from flext_infra._utilities.formatting import (
        FlextInfraUtilitiesFormatting as FlextInfraUtilitiesFormatting,
    )
    from flext_infra._utilities.git import (
        FlextInfraUtilitiesGit as FlextInfraUtilitiesGit,
    )
    from flext_infra._utilities.github import (
        FlextInfraUtilitiesGithub as FlextInfraUtilitiesGithub,
    )
    from flext_infra._utilities.io import FlextInfraUtilitiesIo as FlextInfraUtilitiesIo
    from flext_infra._utilities.iteration import (
        FlextInfraUtilitiesIteration as FlextInfraUtilitiesIteration,
    )
    from flext_infra._utilities.log_parser import (
        FlextInfraUtilitiesLogParser as FlextInfraUtilitiesLogParser,
    )
    from flext_infra._utilities.output import (
        FlextInfraUtilitiesOutput as FlextInfraUtilitiesOutput,
        output as output,
    )
    from flext_infra._utilities.parsing import (
        FlextInfraUtilitiesParsing as FlextInfraUtilitiesParsing,
    )
    from flext_infra._utilities.paths import (
        FlextInfraUtilitiesPaths as FlextInfraUtilitiesPaths,
    )
    from flext_infra._utilities.patterns import (
        FlextInfraUtilitiesPatterns as FlextInfraUtilitiesPatterns,
    )
    from flext_infra._utilities.release import (
        FlextInfraUtilitiesRelease as FlextInfraUtilitiesRelease,
    )
    from flext_infra._utilities.reporting import (
        FlextInfraUtilitiesReporting as FlextInfraUtilitiesReporting,
    )
    from flext_infra._utilities.rope import (
        FlextInfraUtilitiesRope as FlextInfraUtilitiesRope,
    )
    from flext_infra._utilities.safety import (
        FlextInfraUtilitiesSafety as FlextInfraUtilitiesSafety,
    )
    from flext_infra._utilities.selection import (
        FlextInfraUtilitiesSelection as FlextInfraUtilitiesSelection,
    )
    from flext_infra._utilities.subprocess import (
        FlextInfraUtilitiesSubprocess as FlextInfraUtilitiesSubprocess,
    )
    from flext_infra._utilities.templates import (
        FlextInfraUtilitiesTemplates as FlextInfraUtilitiesTemplates,
    )
    from flext_infra._utilities.terminal import (
        FlextInfraUtilitiesTerminal as FlextInfraUtilitiesTerminal,
    )
    from flext_infra._utilities.toml import (
        FlextInfraUtilitiesToml as FlextInfraUtilitiesToml,
    )
    from flext_infra._utilities.toml_parse import (
        FlextInfraUtilitiesTomlParse as FlextInfraUtilitiesTomlParse,
    )
    from flext_infra._utilities.versioning import (
        FlextInfraUtilitiesVersioning as FlextInfraUtilitiesVersioning,
    )
    from flext_infra._utilities.yaml import (
        FlextInfraUtilitiesYaml as FlextInfraUtilitiesYaml,
    )
    from flext_infra.basemk import engine as engine, generator as generator
    from flext_infra.basemk._constants import (
        FlextInfraBasemkConstants as FlextInfraBasemkConstants,
    )
    from flext_infra.basemk._models import (
        FlextInfraBasemkModels as FlextInfraBasemkModels,
    )
    from flext_infra.basemk.cli import FlextInfraCliBasemk as FlextInfraCliBasemk
    from flext_infra.basemk.engine import (
        FlextInfraBaseMkTemplateEngine as FlextInfraBaseMkTemplateEngine,
    )
    from flext_infra.basemk.generator import (
        FlextInfraBaseMkGenerator as FlextInfraBaseMkGenerator,
    )
    from flext_infra.check import (
        services as services,
        workspace_check as workspace_check,
    )
    from flext_infra.check._constants import (
        FlextInfraCheckConstants as FlextInfraCheckConstants,
    )
    from flext_infra.check._models import FlextInfraCheckModels as FlextInfraCheckModels
    from flext_infra.check.cli import FlextInfraCliCheck as FlextInfraCliCheck
    from flext_infra.check.services import (
        FlextInfraConfigFixer as FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker as FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check import (
        build_parser as build_parser,
        run_cli as run_cli,
    )
    from flext_infra.cli import FlextInfraCli as FlextInfraCli, main as main
    from flext_infra.codegen import (
        constants_quality_gate as constants_quality_gate,
        fixer as fixer,
        lazy_init as lazy_init,
        py_typed as py_typed,
        scaffolder as scaffolder,
    )
    from flext_infra.codegen._codegen_coercion import (
        FlextInfraCodegenCoercion as FlextInfraCodegenCoercion,
    )
    from flext_infra.codegen._codegen_execution_tools import (
        FlextInfraCodegenExecutionTools as FlextInfraCodegenExecutionTools,
    )
    from flext_infra.codegen._codegen_generation import (
        FlextInfraCodegenGeneration as FlextInfraCodegenGeneration,
    )
    from flext_infra.codegen._codegen_metrics import (
        FlextInfraCodegenMetrics as FlextInfraCodegenMetrics,
    )
    from flext_infra.codegen._codegen_metrics_checks import (
        FlextInfraCodegenMetricsChecks as FlextInfraCodegenMetricsChecks,
    )
    from flext_infra.codegen._codegen_snapshot import (
        FlextInfraCodegenSnapshot as FlextInfraCodegenSnapshot,
    )
    from flext_infra.codegen._constants import (
        FlextInfraCodegenConstants as FlextInfraCodegenConstants,
    )
    from flext_infra.codegen._models import (
        FlextInfraCodegenModels as FlextInfraCodegenModels,
    )
    from flext_infra.codegen._utilities import (
        FlextInfraUtilitiesCodegen as FlextInfraUtilitiesCodegen,
    )
    from flext_infra.codegen._utilities_codegen_ast_parsing import (
        FlextInfraUtilitiesCodegenAstParsing as FlextInfraUtilitiesCodegenAstParsing,
    )
    from flext_infra.codegen._utilities_codegen_constant_transformer import (
        FlextInfraUtilitiesCodegenConstantTransformation as FlextInfraUtilitiesCodegenConstantTransformation,
    )
    from flext_infra.codegen._utilities_codegen_constant_visitor import (
        FlextInfraUtilitiesCodegenConstantDetection as FlextInfraUtilitiesCodegenConstantDetection,
    )
    from flext_infra.codegen._utilities_codegen_execution import (
        FlextInfraUtilitiesCodegenExecution as FlextInfraUtilitiesCodegenExecution,
    )
    from flext_infra.codegen._utilities_codegen_governance import (
        FlextInfraUtilitiesCodegenGovernance as FlextInfraUtilitiesCodegenGovernance,
    )
    from flext_infra.codegen._utilities_transforms import (
        FlextInfraUtilitiesCodegenTransforms as FlextInfraUtilitiesCodegenTransforms,
    )
    from flext_infra.codegen.census import (
        FlextInfraCodegenCensus as FlextInfraCodegenCensus,
    )
    from flext_infra.codegen.cli import FlextInfraCliCodegen as FlextInfraCliCodegen
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenConstantsQualityGate as FlextInfraCodegenConstantsQualityGate,
    )
    from flext_infra.codegen.fixer import (
        FlextInfraCodegenFixer as FlextInfraCodegenFixer,
    )
    from flext_infra.codegen.lazy_init import (
        FlextInfraCodegenLazyInit as FlextInfraCodegenLazyInit,
    )
    from flext_infra.codegen.py_typed import (
        FlextInfraCodegenPyTyped as FlextInfraCodegenPyTyped,
    )
    from flext_infra.codegen.scaffolder import (
        FlextInfraCodegenScaffolder as FlextInfraCodegenScaffolder,
    )
    from flext_infra.constants import (
        FlextInfraConstants as FlextInfraConstants,
        FlextInfraConstants as c,
    )
    from flext_infra.deps import (
        detection as detection,
        detector as detector,
        extra_paths as extra_paths,
        fix_pyrefly_config as fix_pyrefly_config,
        internal_sync as internal_sync,
        modernizer as modernizer,
        path_sync as path_sync,
    )
    from flext_infra.deps._constants import (
        FlextInfraDepsConstants as FlextInfraDepsConstants,
    )
    from flext_infra.deps._detector_runtime import (
        FlextInfraDependencyDetectorRuntime as FlextInfraDependencyDetectorRuntime,
    )
    from flext_infra.deps._models import FlextInfraDepsModels as FlextInfraDepsModels
    from flext_infra.deps._phases import (
        consolidate_groups as consolidate_groups,
        ensure_coverage as ensure_coverage,
        ensure_extra_paths as ensure_extra_paths,
        ensure_formatting as ensure_formatting,
        ensure_mypy as ensure_mypy,
        ensure_namespace as ensure_namespace,
        ensure_pydantic_mypy as ensure_pydantic_mypy,
        ensure_pyrefly as ensure_pyrefly,
        ensure_pyright as ensure_pyright,
        ensure_pytest as ensure_pytest,
        ensure_ruff as ensure_ruff,
        inject_comments as inject_comments,
    )
    from flext_infra.deps._phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps._phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps._phases.ensure_extra_paths import (
        FlextInfraEnsureExtraPathsPhase as FlextInfraEnsureExtraPathsPhase,
    )
    from flext_infra.deps._phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps._phases.ensure_mypy import (
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pytest import (
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps._phases.ensure_ruff import (
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps._phases.inject_comments import (
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )
    from flext_infra.deps.cli import FlextInfraCliDeps as FlextInfraCliDeps
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionService as FlextInfraDependencyDetectionService,
    )
    from flext_infra.deps.detector import (
        FlextInfraRuntimeDevDependencyDetector as FlextInfraRuntimeDevDependencyDetector,
    )
    from flext_infra.deps.extra_paths import (
        FlextInfraExtraPathsManager as FlextInfraExtraPathsManager,
    )
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService as FlextInfraInternalDependencySyncService,
    )
    from flext_infra.deps.modernizer import (
        FlextInfraPyprojectModernizer as FlextInfraPyprojectModernizer,
    )
    from flext_infra.deps.path_sync import (
        FlextInfraDependencyPathSync as FlextInfraDependencyPathSync,
    )
    from flext_infra.detectors import (
        class_placement_detector as class_placement_detector,
        compatibility_alias_detector as compatibility_alias_detector,
        cyclic_import_detector as cyclic_import_detector,
        dependency_analyzer_base as dependency_analyzer_base,
        future_annotations_detector as future_annotations_detector,
        import_alias_detector as import_alias_detector,
        import_collector as import_collector,
        internal_import_detector as internal_import_detector,
        loose_object_detector as loose_object_detector,
        manual_protocol_detector as manual_protocol_detector,
        manual_typing_alias_detector as manual_typing_alias_detector,
        mro_completeness_detector as mro_completeness_detector,
        namespace_facade_scanner as namespace_facade_scanner,
        namespace_source_detector as namespace_source_detector,
        runtime_alias_detector as runtime_alias_detector,
    )
    from flext_infra.detectors._base_detector import (
        FlextInfraScanFileMixin as FlextInfraScanFileMixin,
        _DetectorContext as _DetectorContext,
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
    from flext_infra.detectors.dependency_analyzer_base import (
        FlextInfraDependencyAnalyzer as FlextInfraDependencyAnalyzer,
    )
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector as FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector as FlextInfraImportAliasDetector,
    )
    from flext_infra.detectors.import_collector import (
        FlextInfraImportCollector as FlextInfraImportCollector,
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
    from flext_infra.detectors.namespace_facade_scanner import (
        FlextInfraNamespaceFacadeScanner as FlextInfraNamespaceFacadeScanner,
    )
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector as FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector as FlextInfraRuntimeAliasDetector,
    )
    from flext_infra.docs import (
        auditor as auditor,
        builder as builder,
        validator as validator,
    )
    from flext_infra.docs._constants import (
        FlextInfraDocsConstants as FlextInfraDocsConstants,
    )
    from flext_infra.docs._models import FlextInfraDocsModels as FlextInfraDocsModels
    from flext_infra.docs.auditor import FlextInfraDocAuditor as FlextInfraDocAuditor
    from flext_infra.docs.builder import FlextInfraDocBuilder as FlextInfraDocBuilder
    from flext_infra.docs.cli import (
        FlextInfraCliDocs as FlextInfraCliDocs,
        FlextInfraDocsCli as FlextInfraDocsCli,
    )
    from flext_infra.docs.fixer import FlextInfraDocFixer as FlextInfraDocFixer
    from flext_infra.docs.generator import (
        FlextInfraDocGenerator as FlextInfraDocGenerator,
    )
    from flext_infra.docs.validator import (
        FlextInfraDocValidator as FlextInfraDocValidator,
    )
    from flext_infra.gates import (
        bandit as bandit,
        go as go,
        markdown as markdown,
        mypy as mypy,
        pyrefly as pyrefly,
        pyright as pyright,
        ruff_format as ruff_format,
        ruff_lint as ruff_lint,
    )
    from flext_infra.gates._base_gate import FlextInfraGate as FlextInfraGate
    from flext_infra.gates._gate_registry import (
        FlextInfraGateRegistry as FlextInfraGateRegistry,
    )
    from flext_infra.gates._models import FlextInfraGatesModels as FlextInfraGatesModels
    from flext_infra.gates.bandit import FlextInfraBanditGate as FlextInfraBanditGate
    from flext_infra.gates.go import FlextInfraGoGate as FlextInfraGoGate
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
    from flext_infra.github._constants import (
        FlextInfraGithubConstants as FlextInfraGithubConstants,
    )
    from flext_infra.github._models import (
        FlextInfraGithubModels as FlextInfraGithubModels,
    )
    from flext_infra.github.cli import FlextInfraCliGithub as FlextInfraCliGithub
    from flext_infra.models import (
        FlextInfraModels as FlextInfraModels,
        FlextInfraModels as m,
    )
    from flext_infra.protocols import (
        FlextInfraProtocols as FlextInfraProtocols,
        FlextInfraProtocols as p,
    )
    from flext_infra.refactor import (
        class_nesting_analyzer as class_nesting_analyzer,
        migrate_to_class_mro as migrate_to_class_mro,
        mro_import_rewriter as mro_import_rewriter,
        mro_migration_validator as mro_migration_validator,
        mro_resolver as mro_resolver,
        namespace_enforcer as namespace_enforcer,
        project_classifier as project_classifier,
        rule as rule,
        rule_definition_validator as rule_definition_validator,
        scanner as scanner,
        violation_analyzer as violation_analyzer,
    )
    from flext_infra.refactor._base_rule import (
        CONTAINER_DICT_SEQ_ADAPTER as CONTAINER_DICT_SEQ_ADAPTER,
        INFRA_MAPPING_ADAPTER as INFRA_MAPPING_ADAPTER,
        INFRA_SEQ_ADAPTER as INFRA_SEQ_ADAPTER,
        STR_MAPPING_ADAPTER as STR_MAPPING_ADAPTER,
        FlextInfraChangeTracker as FlextInfraChangeTracker,
        FlextInfraGenericTransformerRule as FlextInfraGenericTransformerRule,
        FlextInfraRefactorRule as FlextInfraRefactorRule,
    )
    from flext_infra.refactor._constants import (
        FlextInfraRefactorConstants as FlextInfraRefactorConstants,
    )
    from flext_infra.refactor._function_dependency_collector import (
        FlextInfraFunctionDependencyCollector as FlextInfraFunctionDependencyCollector,
    )
    from flext_infra.refactor._import_dependency_collector import (
        FlextInfraImportDependencyCollector as FlextInfraImportDependencyCollector,
    )
    from flext_infra.refactor._models import (
        FlextInfraRefactorModels as FlextInfraRefactorModels,
    )
    from flext_infra.refactor._models_ast_grep import (
        FlextInfraRefactorAstGrepModels as FlextInfraRefactorAstGrepModels,
    )
    from flext_infra.refactor._models_namespace_enforcer import (
        FlextInfraNamespaceEnforcerModels as FlextInfraNamespaceEnforcerModels,
    )
    from flext_infra.refactor._post_check_gate import (
        FlextInfraPostCheckGate as FlextInfraPostCheckGate,
    )
    from flext_infra.refactor._top_level_class_collector import (
        FlextInfraTopLevelClassCollector as FlextInfraTopLevelClassCollector,
    )
    from flext_infra.refactor._typings import (
        FlextInfraRectorTypes as FlextInfraRectorTypes,
    )
    from flext_infra.refactor._utilities import (
        FlextInfraUtilitiesRefactor as FlextInfraUtilitiesRefactor,
    )
    from flext_infra.refactor._utilities_cli import (
        FlextInfraUtilitiesRefactorCli as FlextInfraUtilitiesRefactorCli,
    )
    from flext_infra.refactor._utilities_loader import (
        FlextInfraUtilitiesRefactorLoader as FlextInfraUtilitiesRefactorLoader,
    )
    from flext_infra.refactor._utilities_mro_scan import (
        FlextInfraUtilitiesRefactorMroScan as FlextInfraUtilitiesRefactorMroScan,
    )
    from flext_infra.refactor._utilities_mro_transform import (
        FlextInfraUtilitiesRefactorMroTransform as FlextInfraUtilitiesRefactorMroTransform,
    )
    from flext_infra.refactor._utilities_namespace import (
        FlextInfraUtilitiesRefactorNamespace as FlextInfraUtilitiesRefactorNamespace,
    )
    from flext_infra.refactor._utilities_pydantic import (
        FlextInfraUtilitiesRefactorPydantic as FlextInfraUtilitiesRefactorPydantic,
    )
    from flext_infra.refactor._utilities_pydantic_analysis import (
        FlextInfraUtilitiesRefactorPydanticAnalysis as FlextInfraUtilitiesRefactorPydanticAnalysis,
    )
    from flext_infra.refactor.census import (
        FlextInfraRefactorCensus as FlextInfraRefactorCensus,
    )
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer as FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.cli import FlextInfraCliRefactor as FlextInfraCliRefactor
    from flext_infra.refactor.engine import (
        FlextInfraRefactorClassReconstructorRule as FlextInfraRefactorClassReconstructorRule,
        FlextInfraRefactorEngine as FlextInfraRefactorEngine,
        FlextInfraRefactorMRORedundancyChecker as FlextInfraRefactorMRORedundancyChecker,
        FlextInfraRefactorSignaturePropagationRule as FlextInfraRefactorSignaturePropagationRule,
        FlextInfraRefactorSymbolPropagationRule as FlextInfraRefactorSymbolPropagationRule,
        FlextInfraRefactorTier0ImportFixRule as FlextInfraRefactorTier0ImportFixRule,
        FlextInfraRefactorTypingAnnotationFixRule as FlextInfraRefactorTypingAnnotationFixRule,
        FlextInfraRefactorTypingUnificationRule as FlextInfraRefactorTypingUnificationRule,
    )
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO as FlextInfraRefactorMigrateToClassMRO,
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
    from flext_infra.refactor.project_classifier import (
        FlextInfraProjectClassifier as FlextInfraProjectClassifier,
    )
    from flext_infra.refactor.rule import (
        FlextInfraRefactorRuleLoader as FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.rule_definition_validator import (
        FlextInfraRefactorRuleDefinitionValidator as FlextInfraRefactorRuleDefinitionValidator,
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
    from flext_infra.release import orchestrator as orchestrator
    from flext_infra.release._constants import (
        FlextInfraReleaseConstants as FlextInfraReleaseConstants,
    )
    from flext_infra.release._models import (
        FlextInfraReleaseModels as FlextInfraReleaseModels,
    )
    from flext_infra.release.cli import FlextInfraCliRelease as FlextInfraCliRelease
    from flext_infra.release.orchestrator import (
        FlextInfraReleaseOrchestrator as FlextInfraReleaseOrchestrator,
    )
    from flext_infra.rules import (
        class_nesting as class_nesting,
        class_reconstructor as class_reconstructor,
        ensure_future_annotations as ensure_future_annotations,
        import_modernizer as import_modernizer,
        legacy_removal as legacy_removal,
        mro_class_migration as mro_class_migration,
        pattern_corrections as pattern_corrections,
    )
    from flext_infra.rules.class_nesting import (
        FlextInfraClassNestingRefactorRule as FlextInfraClassNestingRefactorRule,
    )
    from flext_infra.rules.class_reconstructor import (
        FlextInfraPreCheckGate as FlextInfraPreCheckGate,
        FlextInfraRefactorClassNestingReconstructor as FlextInfraRefactorClassNestingReconstructor,
    )
    from flext_infra.rules.ensure_future_annotations import (
        FlextInfraRefactorEnsureFutureAnnotationsRule as FlextInfraRefactorEnsureFutureAnnotationsRule,
    )
    from flext_infra.rules.import_modernizer import (
        FlextInfraRefactorImportModernizerRule as FlextInfraRefactorImportModernizerRule,
    )
    from flext_infra.rules.legacy_removal import (
        FlextInfraRefactorLegacyRemovalRule as FlextInfraRefactorLegacyRemovalRule,
    )
    from flext_infra.rules.mro_class_migration import (
        FlextInfraRefactorMROClassMigrationRule as FlextInfraRefactorMROClassMigrationRule,
    )
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule as FlextInfraRefactorPatternCorrectionsRule,
    )
    from flext_infra.transformers import (
        alias_remover as alias_remover,
        census_visitors as census_visitors,
        deprecated_remover as deprecated_remover,
        dict_to_mapping as dict_to_mapping,
        helper_consolidation as helper_consolidation,
        import_bypass_remover as import_bypass_remover,
        lazy_import_fixer as lazy_import_fixer,
        mro_private_inline as mro_private_inline,
        mro_remover as mro_remover,
        mro_symbol_propagator as mro_symbol_propagator,
        nested_class_propagation as nested_class_propagation,
        policy as policy,
        redundant_cast_remover as redundant_cast_remover,
        signature_propagator as signature_propagator,
        symbol_propagator as symbol_propagator,
        tier0_import_fixer as tier0_import_fixer,
        typing_annotation_replacer as typing_annotation_replacer,
        typing_unifier as typing_unifier,
        violation_census_visitor as violation_census_visitor,
    )
    from flext_infra.transformers._base import (
        FlextInfraChangeTrackingTransformer as FlextInfraChangeTrackingTransformer,
    )
    from flext_infra.transformers._utilities_normalizer import (
        FlextInfraNormalizerContext as FlextInfraNormalizerContext,
        FlextInfraUtilitiesImportNormalizer as FlextInfraUtilitiesImportNormalizer,
    )
    from flext_infra.transformers.alias_remover import (
        FlextInfraRefactorAliasRemover as FlextInfraRefactorAliasRemover,
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
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover as FlextInfraRefactorDeprecatedRemover,
    )
    from flext_infra.transformers.dict_to_mapping import (
        FlextInfraDictToMappingTransformer as FlextInfraDictToMappingTransformer,
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
    from flext_infra.transformers.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer as FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer as FlextInfraRefactorMROQualifiedReferenceTransformer,
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
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities as FlextInfraRefactorTransformerPolicyUtilities,
    )
    from flext_infra.transformers.redundant_cast_remover import (
        FlextInfraRedundantCastRemover as FlextInfraRedundantCastRemover,
    )
    from flext_infra.transformers.signature_propagator import (
        FlextInfraRefactorSignaturePropagator as FlextInfraRefactorSignaturePropagator,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator as FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer as FlextInfraTransformerTier0ImportFixer,
    )
    from flext_infra.transformers.typing_annotation_replacer import (
        FlextInfraTypingAnnotationReplacer as FlextInfraTypingAnnotationReplacer,
    )
    from flext_infra.transformers.typing_unifier import (
        FlextInfraRefactorTypingUnifier as FlextInfraRefactorTypingUnifier,
    )
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor as FlextInfraViolationCensusVisitor,
    )
    from flext_infra.typings import (
        FlextInfraTypes as FlextInfraTypes,
        FlextInfraTypes as t,
    )
    from flext_infra.utilities import (
        FlextInfraUtilities as FlextInfraUtilities,
        FlextInfraUtilities as u,
    )
    from flext_infra.validate import (
        basemk_validator as basemk_validator,
        inventory as inventory,
        namespace_validator as namespace_validator,
        pytest_diag as pytest_diag,
        skill_validator as skill_validator,
        stub_chain as stub_chain,
    )
    from flext_infra.validate._constants import (
        FlextInfraCoreConstants as FlextInfraCoreConstants,
        FlextInfraSharedInfraConstants as FlextInfraSharedInfraConstants,
    )
    from flext_infra.validate._models import (
        FlextInfraCoreModels as FlextInfraCoreModels,
    )
    from flext_infra.validate.basemk_validator import (
        FlextInfraBaseMkValidator as FlextInfraBaseMkValidator,
    )
    from flext_infra.validate.cli import FlextInfraCliValidate as FlextInfraCliValidate
    from flext_infra.validate.inventory import (
        FlextInfraInventoryService as FlextInfraInventoryService,
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
    from flext_infra.validate.skill_validator import (
        FlextInfraSkillValidator as FlextInfraSkillValidator,
    )
    from flext_infra.validate.stub_chain import (
        FlextInfraStubSupplyChain as FlextInfraStubSupplyChain,
    )
    from flext_infra.workspace import (
        maintenance as maintenance,
        migrator as migrator,
        project_makefile as project_makefile,
        sync as sync,
        workspace_makefile as workspace_makefile,
    )
    from flext_infra.workspace._constants import (
        FlextInfraWorkspaceConstants as FlextInfraWorkspaceConstants,
    )
    from flext_infra.workspace._models import (
        FlextInfraWorkspaceModels as FlextInfraWorkspaceModels,
    )
    from flext_infra.workspace.cli import (
        FlextInfraCliWorkspace as FlextInfraCliWorkspace,
    )
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector as FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMode as FlextInfraWorkspaceMode,
    )
    from flext_infra.workspace.maintenance import python_version as python_version
    from flext_infra.workspace.maintenance.cli import (
        FlextInfraCliMaintenance as FlextInfraCliMaintenance,
    )
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer as FlextInfraPythonVersionEnforcer,
        logger as logger,
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
    from flext_infra.workspace.sync import (
        FlextInfraSyncService as FlextInfraSyncService,
    )
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator as FlextInfraWorkspaceMakefileGenerator,
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
    "FlextInfraCli": ["flext_infra.cli", "FlextInfraCli"],
    "FlextInfraCliBasemk": ["flext_infra.basemk.cli", "FlextInfraCliBasemk"],
    "FlextInfraCliCheck": ["flext_infra.check.cli", "FlextInfraCliCheck"],
    "FlextInfraCliCodegen": ["flext_infra.codegen.cli", "FlextInfraCliCodegen"],
    "FlextInfraCliDeps": ["flext_infra.deps.cli", "FlextInfraCliDeps"],
    "FlextInfraCliDocs": ["flext_infra.docs.cli", "FlextInfraCliDocs"],
    "FlextInfraCliGithub": ["flext_infra.github.cli", "FlextInfraCliGithub"],
    "FlextInfraCliMaintenance": [
        "flext_infra.workspace.maintenance.cli",
        "FlextInfraCliMaintenance",
    ],
    "FlextInfraCliRefactor": ["flext_infra.refactor.cli", "FlextInfraCliRefactor"],
    "FlextInfraCliRelease": ["flext_infra.release.cli", "FlextInfraCliRelease"],
    "FlextInfraCliValidate": ["flext_infra.validate.cli", "FlextInfraCliValidate"],
    "FlextInfraCliWorkspace": ["flext_infra.workspace.cli", "FlextInfraCliWorkspace"],
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
    "FlextInfraConstantsCensus": [
        "flext_infra._constants.census",
        "FlextInfraConstantsCensus",
    ],
    "FlextInfraConstantsCst": ["flext_infra._constants.cst", "FlextInfraConstantsCst"],
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
    "FlextInfraDictToMappingTransformer": [
        "flext_infra.transformers.dict_to_mapping",
        "FlextInfraDictToMappingTransformer",
    ],
    "FlextInfraDocAuditor": ["flext_infra.docs.auditor", "FlextInfraDocAuditor"],
    "FlextInfraDocBuilder": ["flext_infra.docs.builder", "FlextInfraDocBuilder"],
    "FlextInfraDocFixer": ["flext_infra.docs.fixer", "FlextInfraDocFixer"],
    "FlextInfraDocGenerator": ["flext_infra.docs.generator", "FlextInfraDocGenerator"],
    "FlextInfraDocValidator": ["flext_infra.docs.validator", "FlextInfraDocValidator"],
    "FlextInfraDocsCli": ["flext_infra.docs.cli", "FlextInfraDocsCli"],
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
    "FlextInfraModelsCensus": ["flext_infra._models.census", "FlextInfraModelsCensus"],
    "FlextInfraModelsCliInputs": [
        "flext_infra._models.cli_inputs",
        "FlextInfraModelsCliInputs",
    ],
    "FlextInfraModelsCst": ["flext_infra._models.cst", "FlextInfraModelsCst"],
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
    "FlextInfraProtocolsCst": ["flext_infra._protocols.cst", "FlextInfraProtocolsCst"],
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
    "FlextInfraRedundantCastRemover": [
        "flext_infra.transformers.redundant_cast_remover",
        "FlextInfraRedundantCastRemover",
    ],
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
        "flext_infra.refactor.engine",
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
        "flext_infra.refactor.engine",
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
        "flext_infra.refactor.engine",
        "FlextInfraRefactorSignaturePropagationRule",
    ],
    "FlextInfraRefactorSignaturePropagator": [
        "flext_infra.transformers.signature_propagator",
        "FlextInfraRefactorSignaturePropagator",
    ],
    "FlextInfraRefactorSymbolPropagationRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorSymbolPropagationRule",
    ],
    "FlextInfraRefactorSymbolPropagator": [
        "flext_infra.transformers.symbol_propagator",
        "FlextInfraRefactorSymbolPropagator",
    ],
    "FlextInfraRefactorTier0ImportFixRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorTier0ImportFixRule",
    ],
    "FlextInfraRefactorTransformerPolicyUtilities": [
        "flext_infra.transformers.policy",
        "FlextInfraRefactorTransformerPolicyUtilities",
    ],
    "FlextInfraRefactorTypingAnnotationFixRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorTypingAnnotationFixRule",
    ],
    "FlextInfraRefactorTypingUnificationRule": [
        "flext_infra.refactor.engine",
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
    "FlextInfraTypesCst": ["flext_infra._typings.cst", "FlextInfraTypesCst"],
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
    "FlextInfraUtilitiesCst": ["flext_infra._utilities.cst", "FlextInfraUtilitiesCst"],
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
    "_DetectorContext": ["flext_infra.detectors._base_detector", "_DetectorContext"],
    "_constants": ["flext_infra._constants", ""],
    "_models": ["flext_infra._models", ""],
    "_protocols": ["flext_infra._protocols", ""],
    "_typings": ["flext_infra._typings", ""],
    "_utilities": ["flext_infra._utilities", ""],
    "alias_remover": ["flext_infra.transformers.alias_remover", ""],
    "auditor": ["flext_infra.docs.auditor", ""],
    "bandit": ["flext_infra.gates.bandit", ""],
    "base": ["flext_infra._constants.base", ""],
    "basemk": ["flext_infra.basemk", ""],
    "basemk_validator": ["flext_infra.validate.basemk_validator", ""],
    "build_parser": ["flext_infra.check.workspace_check", "build_parser"],
    "builder": ["flext_infra.docs.builder", ""],
    "c": ["flext_infra.constants", "FlextInfraConstants"],
    "census": ["flext_infra._constants.census", ""],
    "census_visitors": ["flext_infra.transformers.census_visitors", ""],
    "check": ["flext_infra.check", ""],
    "class_nesting": ["flext_infra.rules.class_nesting", ""],
    "class_nesting_analyzer": ["flext_infra.refactor.class_nesting_analyzer", ""],
    "class_placement_detector": ["flext_infra.detectors.class_placement_detector", ""],
    "class_reconstructor": ["flext_infra.rules.class_reconstructor", ""],
    "cli": ["flext_infra.cli", ""],
    "cli_inputs": ["flext_infra._models.cli_inputs", ""],
    "codegen": ["flext_infra.codegen", ""],
    "compatibility_alias_detector": [
        "flext_infra.detectors.compatibility_alias_detector",
        "",
    ],
    "consolidate_groups": ["flext_infra.deps._phases.consolidate_groups", ""],
    "constants": ["flext_infra.constants", ""],
    "constants_quality_gate": ["flext_infra.codegen.constants_quality_gate", ""],
    "cst": ["flext_infra._constants.cst", ""],
    "cyclic_import_detector": ["flext_infra.detectors.cyclic_import_detector", ""],
    "d": ["flext_cli", "d"],
    "dependency_analyzer_base": ["flext_infra.detectors.dependency_analyzer_base", ""],
    "deprecated_remover": ["flext_infra.transformers.deprecated_remover", ""],
    "deps": ["flext_infra.deps", ""],
    "detection": ["flext_infra.deps.detection", ""],
    "detector": ["flext_infra.deps.detector", ""],
    "detectors": ["flext_infra.detectors", ""],
    "dict_to_mapping": ["flext_infra.transformers.dict_to_mapping", ""],
    "discovery": ["flext_infra._utilities.discovery", ""],
    "docs": ["flext_infra._utilities.docs", ""],
    "e": ["flext_cli", "e"],
    "engine": ["flext_infra.basemk.engine", ""],
    "ensure_coverage": ["flext_infra.deps._phases.ensure_coverage", ""],
    "ensure_extra_paths": ["flext_infra.deps._phases.ensure_extra_paths", ""],
    "ensure_formatting": ["flext_infra.deps._phases.ensure_formatting", ""],
    "ensure_future_annotations": ["flext_infra.rules.ensure_future_annotations", ""],
    "ensure_mypy": ["flext_infra.deps._phases.ensure_mypy", ""],
    "ensure_namespace": ["flext_infra.deps._phases.ensure_namespace", ""],
    "ensure_pydantic_mypy": ["flext_infra.deps._phases.ensure_pydantic_mypy", ""],
    "ensure_pyrefly": ["flext_infra.deps._phases.ensure_pyrefly", ""],
    "ensure_pyright": ["flext_infra.deps._phases.ensure_pyright", ""],
    "ensure_pytest": ["flext_infra.deps._phases.ensure_pytest", ""],
    "ensure_ruff": ["flext_infra.deps._phases.ensure_ruff", ""],
    "extra_paths": ["flext_infra.deps.extra_paths", ""],
    "fix_pyrefly_config": ["flext_infra.deps.fix_pyrefly_config", ""],
    "fixer": ["flext_infra.codegen.fixer", ""],
    "formatting": ["flext_infra._utilities.formatting", ""],
    "future_annotations_detector": [
        "flext_infra.detectors.future_annotations_detector",
        "",
    ],
    "gates": ["flext_infra.gates", ""],
    "generator": ["flext_infra.basemk.generator", ""],
    "git": ["flext_infra._utilities.git", ""],
    "github": ["flext_infra._utilities.github", ""],
    "go": ["flext_infra.gates.go", ""],
    "h": ["flext_cli", "h"],
    "helper_consolidation": ["flext_infra.transformers.helper_consolidation", ""],
    "import_alias_detector": ["flext_infra.detectors.import_alias_detector", ""],
    "import_bypass_remover": ["flext_infra.transformers.import_bypass_remover", ""],
    "import_collector": ["flext_infra.detectors.import_collector", ""],
    "import_modernizer": ["flext_infra.rules.import_modernizer", ""],
    "inject_comments": ["flext_infra.deps._phases.inject_comments", ""],
    "internal_import_detector": ["flext_infra.detectors.internal_import_detector", ""],
    "internal_sync": ["flext_infra.deps.internal_sync", ""],
    "inventory": ["flext_infra.validate.inventory", ""],
    "io": ["flext_infra._utilities.io", ""],
    "iteration": ["flext_infra._utilities.iteration", ""],
    "lazy_import_fixer": ["flext_infra.transformers.lazy_import_fixer", ""],
    "lazy_init": ["flext_infra.codegen.lazy_init", ""],
    "legacy_removal": ["flext_infra.rules.legacy_removal", ""],
    "log_parser": ["flext_infra._utilities.log_parser", ""],
    "logger": ["flext_infra.workspace.maintenance.python_version", "logger"],
    "loose_object_detector": ["flext_infra.detectors.loose_object_detector", ""],
    "m": ["flext_infra.models", "FlextInfraModels"],
    "main": ["flext_infra.cli", "main"],
    "maintenance": ["flext_infra.workspace.maintenance", ""],
    "manual_protocol_detector": ["flext_infra.detectors.manual_protocol_detector", ""],
    "manual_typing_alias_detector": [
        "flext_infra.detectors.manual_typing_alias_detector",
        "",
    ],
    "markdown": ["flext_infra.gates.markdown", ""],
    "migrate_to_class_mro": ["flext_infra.refactor.migrate_to_class_mro", ""],
    "migrator": ["flext_infra.workspace.migrator", ""],
    "models": ["flext_infra.models", ""],
    "modernizer": ["flext_infra.deps.modernizer", ""],
    "mro_class_migration": ["flext_infra.rules.mro_class_migration", ""],
    "mro_completeness_detector": [
        "flext_infra.detectors.mro_completeness_detector",
        "",
    ],
    "mro_import_rewriter": ["flext_infra.refactor.mro_import_rewriter", ""],
    "mro_migration_validator": ["flext_infra.refactor.mro_migration_validator", ""],
    "mro_private_inline": ["flext_infra.transformers.mro_private_inline", ""],
    "mro_remover": ["flext_infra.transformers.mro_remover", ""],
    "mro_resolver": ["flext_infra.refactor.mro_resolver", ""],
    "mro_symbol_propagator": ["flext_infra.transformers.mro_symbol_propagator", ""],
    "mypy": ["flext_infra.gates.mypy", ""],
    "namespace_enforcer": ["flext_infra.refactor.namespace_enforcer", ""],
    "namespace_facade_scanner": ["flext_infra.detectors.namespace_facade_scanner", ""],
    "namespace_source_detector": [
        "flext_infra.detectors.namespace_source_detector",
        "",
    ],
    "namespace_validator": ["flext_infra.validate.namespace_validator", ""],
    "nested_class_propagation": [
        "flext_infra.transformers.nested_class_propagation",
        "",
    ],
    "orchestrator": ["flext_infra.release.orchestrator", ""],
    "output": ["flext_infra._utilities.output", "output"],
    "p": ["flext_infra.protocols", "FlextInfraProtocols"],
    "parsing": ["flext_infra._utilities.parsing", ""],
    "path_sync": ["flext_infra.deps.path_sync", ""],
    "paths": ["flext_infra._utilities.paths", ""],
    "pattern_corrections": ["flext_infra.rules.pattern_corrections", ""],
    "patterns": ["flext_infra._utilities.patterns", ""],
    "policy": ["flext_infra.transformers.policy", ""],
    "project_classifier": ["flext_infra.refactor.project_classifier", ""],
    "project_makefile": ["flext_infra.workspace.project_makefile", ""],
    "protocols": ["flext_infra.protocols", ""],
    "py_typed": ["flext_infra.codegen.py_typed", ""],
    "pyrefly": ["flext_infra.gates.pyrefly", ""],
    "pyright": ["flext_infra.gates.pyright", ""],
    "pytest_diag": ["flext_infra.validate.pytest_diag", ""],
    "python_version": ["flext_infra.workspace.maintenance.python_version", ""],
    "r": ["flext_cli", "r"],
    "redundant_cast_remover": ["flext_infra.transformers.redundant_cast_remover", ""],
    "refactor": ["flext_infra.refactor", ""],
    "release": ["flext_infra._utilities.release", ""],
    "reporting": ["flext_infra._utilities.reporting", ""],
    "rope": ["flext_infra._constants.rope", ""],
    "ruff_format": ["flext_infra.gates.ruff_format", ""],
    "ruff_lint": ["flext_infra.gates.ruff_lint", ""],
    "rule": ["flext_infra.refactor.rule", ""],
    "rule_definition_validator": ["flext_infra.refactor.rule_definition_validator", ""],
    "rules": ["flext_infra.rules", ""],
    "run_cli": ["flext_infra.check.workspace_check", "run_cli"],
    "runtime_alias_detector": ["flext_infra.detectors.runtime_alias_detector", ""],
    "s": ["flext_cli", "s"],
    "safety": ["flext_infra._utilities.safety", ""],
    "scaffolder": ["flext_infra.codegen.scaffolder", ""],
    "scan": ["flext_infra._models.scan", ""],
    "scanner": ["flext_infra.refactor.scanner", ""],
    "selection": ["flext_infra._utilities.selection", ""],
    "services": ["flext_infra.check.services", ""],
    "signature_propagator": ["flext_infra.transformers.signature_propagator", ""],
    "skill_validator": ["flext_infra.validate.skill_validator", ""],
    "stub_chain": ["flext_infra.validate.stub_chain", ""],
    "subprocess": ["flext_infra._utilities.subprocess", ""],
    "symbol_propagator": ["flext_infra.transformers.symbol_propagator", ""],
    "sync": ["flext_infra.workspace.sync", ""],
    "t": ["flext_infra.typings", "FlextInfraTypes"],
    "templates": ["flext_infra._utilities.templates", ""],
    "terminal": ["flext_infra._utilities.terminal", ""],
    "tier0_import_fixer": ["flext_infra.transformers.tier0_import_fixer", ""],
    "toml": ["flext_infra._utilities.toml", ""],
    "toml_parse": ["flext_infra._utilities.toml_parse", ""],
    "transformers": ["flext_infra.transformers", ""],
    "typing_annotation_replacer": [
        "flext_infra.transformers.typing_annotation_replacer",
        "",
    ],
    "typing_unifier": ["flext_infra.transformers.typing_unifier", ""],
    "typings": ["flext_infra.typings", ""],
    "u": ["flext_infra.utilities", "FlextInfraUtilities"],
    "utilities": ["flext_infra.utilities", ""],
    "validate": ["flext_infra.validate", ""],
    "validator": ["flext_infra.docs.validator", ""],
    "versioning": ["flext_infra._utilities.versioning", ""],
    "violation_analyzer": ["flext_infra.refactor.violation_analyzer", ""],
    "violation_census_visitor": [
        "flext_infra.transformers.violation_census_visitor",
        "",
    ],
    "workspace": ["flext_infra.workspace", ""],
    "workspace_check": ["flext_infra.check.workspace_check", ""],
    "workspace_makefile": ["flext_infra.workspace.workspace_makefile", ""],
    "x": ["flext_cli", "x"],
    "yaml": ["flext_infra._utilities.yaml", ""],
}

_EXPORTS: Sequence[str] = [
    "CONTAINER_DICT_SEQ_ADAPTER",
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
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCst",
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
    "FlextInfraModelsCensus",
    "FlextInfraModelsCliInputs",
    "FlextInfraModelsCst",
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
    "FlextInfraProtocolsCst",
    "FlextInfraProtocolsRope",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraRectorTypes",
    "FlextInfraRedundantCastRemover",
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
    "FlextInfraTypesCst",
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
    "FlextInfraUtilitiesCst",
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
    "FlextInfraVersion",
    "FlextInfraViolationCensusVisitor",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceConstants",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceMakefileGenerator",
    "FlextInfraWorkspaceMode",
    "FlextInfraWorkspaceModels",
    "INFRA_MAPPING_ADAPTER",
    "INFRA_SEQ_ADAPTER",
    "STR_MAPPING_ADAPTER",
    "_DetectorContext",
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
    "codegen",
    "compatibility_alias_detector",
    "consolidate_groups",
    "constants",
    "constants_quality_gate",
    "cst",
    "cyclic_import_detector",
    "d",
    "dependency_analyzer_base",
    "deprecated_remover",
    "deps",
    "detection",
    "detector",
    "detectors",
    "dict_to_mapping",
    "discovery",
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
    "ensure_pytest",
    "ensure_ruff",
    "extra_paths",
    "fix_pyrefly_config",
    "fixer",
    "formatting",
    "future_annotations_detector",
    "gates",
    "generator",
    "git",
    "github",
    "go",
    "h",
    "helper_consolidation",
    "import_alias_detector",
    "import_bypass_remover",
    "import_collector",
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
    "namespace_source_detector",
    "namespace_validator",
    "nested_class_propagation",
    "orchestrator",
    "output",
    "p",
    "parsing",
    "path_sync",
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
    "rope",
    "ruff_format",
    "ruff_lint",
    "rule",
    "rule_definition_validator",
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
    "workspace_makefile",
    "x",
    "yaml",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
