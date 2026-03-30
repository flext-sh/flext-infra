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

if TYPE_CHECKING:
    from flext_cli import *

    from flext_infra import (
        _constants,
        _models,
        _protocols,
        _typings,
        _utilities,
        basemk,
        check,
        cli,
        codegen,
        constants,
        deps,
        detectors,
        gates,
        models,
        protocols,
        refactor,
        rules,
        transformers,
        typings,
        utilities,
        validate,
        workspace,
    )
    from flext_infra._constants import base, census, rope
    from flext_infra._constants.base import *
    from flext_infra._constants.census import *
    from flext_infra._constants.rope import *
    from flext_infra._models import cli_inputs, scan
    from flext_infra._models.base import *
    from flext_infra._models.census import *
    from flext_infra._models.cli_inputs import *
    from flext_infra._models.rope import *
    from flext_infra._models.scan import *
    from flext_infra._protocols.base import *
    from flext_infra._protocols.rope import *
    from flext_infra._typings import cst
    from flext_infra._typings.base import *
    from flext_infra._typings.cst import *
    from flext_infra._typings.rope import *
    from flext_infra._utilities import (
        discovery,
        docs,
        formatting,
        git,
        github,
        io,
        iteration,
        log_parser,
        parsing,
        paths,
        patterns,
        release,
        reporting,
        safety,
        selection,
        subprocess,
        templates,
        terminal,
        toml,
        toml_parse,
        versioning,
        yaml,
    )
    from flext_infra._utilities.base import *
    from flext_infra._utilities.cli import *
    from flext_infra._utilities.cst import *
    from flext_infra._utilities.discovery import *
    from flext_infra._utilities.docs import *
    from flext_infra._utilities.formatting import *
    from flext_infra._utilities.git import *
    from flext_infra._utilities.github import *
    from flext_infra._utilities.io import *
    from flext_infra._utilities.iteration import *
    from flext_infra._utilities.log_parser import *
    from flext_infra._utilities.output import *
    from flext_infra._utilities.parsing import *
    from flext_infra._utilities.paths import *
    from flext_infra._utilities.patterns import *
    from flext_infra._utilities.release import *
    from flext_infra._utilities.reporting import *
    from flext_infra._utilities.rope import *
    from flext_infra._utilities.safety import *
    from flext_infra._utilities.selection import *
    from flext_infra._utilities.subprocess import *
    from flext_infra._utilities.templates import *
    from flext_infra._utilities.terminal import *
    from flext_infra._utilities.toml import *
    from flext_infra._utilities.toml_parse import *
    from flext_infra._utilities.versioning import *
    from flext_infra._utilities.yaml import *
    from flext_infra.basemk import engine, generator
    from flext_infra.basemk._constants import *
    from flext_infra.basemk._models import *
    from flext_infra.basemk.cli import *
    from flext_infra.basemk.engine import *
    from flext_infra.basemk.generator import *
    from flext_infra.check import services, workspace_check
    from flext_infra.check._constants import *
    from flext_infra.check._models import *
    from flext_infra.check.cli import *
    from flext_infra.check.services import *
    from flext_infra.check.workspace_check import *
    from flext_infra.cli import *
    from flext_infra.codegen import (
        constants_quality_gate,
        fixer,
        lazy_init,
        py_typed,
        scaffolder,
    )
    from flext_infra.codegen._codegen_coercion import *
    from flext_infra.codegen._codegen_execution_tools import *
    from flext_infra.codegen._codegen_generation import *
    from flext_infra.codegen._codegen_metrics import *
    from flext_infra.codegen._codegen_metrics_checks import *
    from flext_infra.codegen._codegen_snapshot import *
    from flext_infra.codegen._constants import *
    from flext_infra.codegen._models import *
    from flext_infra.codegen._utilities import *
    from flext_infra.codegen._utilities_codegen_ast_parsing import *
    from flext_infra.codegen._utilities_codegen_constant_transformer import *
    from flext_infra.codegen._utilities_codegen_constant_visitor import *
    from flext_infra.codegen._utilities_codegen_execution import *
    from flext_infra.codegen._utilities_codegen_governance import *
    from flext_infra.codegen._utilities_transforms import *
    from flext_infra.codegen.census import *
    from flext_infra.codegen.cli import *
    from flext_infra.codegen.constants_quality_gate import *
    from flext_infra.codegen.fixer import *
    from flext_infra.codegen.lazy_init import *
    from flext_infra.codegen.py_typed import *
    from flext_infra.codegen.scaffolder import *
    from flext_infra.constants import *
    from flext_infra.deps import (
        detection,
        detector,
        extra_paths,
        fix_pyrefly_config,
        internal_sync,
        modernizer,
        path_sync,
    )
    from flext_infra.deps._constants import *
    from flext_infra.deps._detector_runtime import *
    from flext_infra.deps._models import *
    from flext_infra.deps._phases import (
        consolidate_groups,
        ensure_coverage,
        ensure_extra_paths,
        ensure_formatting,
        ensure_mypy,
        ensure_namespace,
        ensure_pydantic_mypy,
        ensure_pyrefly,
        ensure_pyright,
        ensure_pytest,
        ensure_ruff,
        inject_comments,
    )
    from flext_infra.deps._phases.consolidate_groups import *
    from flext_infra.deps._phases.ensure_coverage import *
    from flext_infra.deps._phases.ensure_extra_paths import *
    from flext_infra.deps._phases.ensure_formatting import *
    from flext_infra.deps._phases.ensure_mypy import *
    from flext_infra.deps._phases.ensure_namespace import *
    from flext_infra.deps._phases.ensure_pydantic_mypy import *
    from flext_infra.deps._phases.ensure_pyrefly import *
    from flext_infra.deps._phases.ensure_pyright import *
    from flext_infra.deps._phases.ensure_pytest import *
    from flext_infra.deps._phases.ensure_ruff import *
    from flext_infra.deps._phases.inject_comments import *
    from flext_infra.deps.cli import *
    from flext_infra.deps.detection import *
    from flext_infra.deps.detector import *
    from flext_infra.deps.extra_paths import *
    from flext_infra.deps.internal_sync import *
    from flext_infra.deps.modernizer import *
    from flext_infra.deps.path_sync import *
    from flext_infra.detectors import (
        class_placement_detector,
        compatibility_alias_detector,
        cyclic_import_detector,
        dependency_analyzer_base,
        future_annotations_detector,
        import_alias_detector,
        import_collector,
        internal_import_detector,
        loose_object_detector,
        manual_protocol_detector,
        manual_typing_alias_detector,
        mro_completeness_detector,
        namespace_facade_scanner,
        namespace_source_detector,
        runtime_alias_detector,
    )
    from flext_infra.detectors._base_detector import *
    from flext_infra.detectors.class_placement_detector import *
    from flext_infra.detectors.compatibility_alias_detector import *
    from flext_infra.detectors.cyclic_import_detector import *
    from flext_infra.detectors.dependency_analyzer_base import *
    from flext_infra.detectors.future_annotations_detector import *
    from flext_infra.detectors.import_alias_detector import *
    from flext_infra.detectors.import_collector import *
    from flext_infra.detectors.internal_import_detector import *
    from flext_infra.detectors.loose_object_detector import *
    from flext_infra.detectors.manual_protocol_detector import *
    from flext_infra.detectors.manual_typing_alias_detector import *
    from flext_infra.detectors.mro_completeness_detector import *
    from flext_infra.detectors.namespace_facade_scanner import *
    from flext_infra.detectors.namespace_source_detector import *
    from flext_infra.detectors.runtime_alias_detector import *
    from flext_infra.docs import auditor, builder, validator
    from flext_infra.docs._constants import *
    from flext_infra.docs._models import *
    from flext_infra.docs.auditor import *
    from flext_infra.docs.builder import *
    from flext_infra.docs.cli import *
    from flext_infra.docs.fixer import *
    from flext_infra.docs.generator import *
    from flext_infra.docs.validator import *
    from flext_infra.gates import (
        bandit,
        go,
        markdown,
        mypy,
        pyrefly,
        pyright,
        ruff_format,
        ruff_lint,
    )
    from flext_infra.gates._base_gate import *
    from flext_infra.gates._gate_registry import *
    from flext_infra.gates._models import *
    from flext_infra.gates.bandit import *
    from flext_infra.gates.go import *
    from flext_infra.gates.markdown import *
    from flext_infra.gates.mypy import *
    from flext_infra.gates.pyrefly import *
    from flext_infra.gates.pyright import *
    from flext_infra.gates.ruff_format import *
    from flext_infra.gates.ruff_lint import *
    from flext_infra.github._constants import *
    from flext_infra.github._models import *
    from flext_infra.github.cli import *
    from flext_infra.models import *
    from flext_infra.protocols import *
    from flext_infra.refactor import (
        class_nesting_analyzer,
        migrate_to_class_mro,
        mro_import_rewriter,
        mro_migration_validator,
        mro_resolver,
        namespace_enforcer,
        project_classifier,
        rule,
        rule_definition_validator,
        scanner,
        violation_analyzer,
    )
    from flext_infra.refactor._base_rule import *
    from flext_infra.refactor._constants import *
    from flext_infra.refactor._function_dependency_collector import *
    from flext_infra.refactor._import_dependency_collector import *
    from flext_infra.refactor._models import *
    from flext_infra.refactor._models_ast_grep import *
    from flext_infra.refactor._models_namespace_enforcer import *
    from flext_infra.refactor._post_check_gate import *
    from flext_infra.refactor._top_level_class_collector import *
    from flext_infra.refactor._utilities import *
    from flext_infra.refactor._utilities_cli import *
    from flext_infra.refactor._utilities_loader import *
    from flext_infra.refactor._utilities_mro_scan import *
    from flext_infra.refactor._utilities_mro_transform import *
    from flext_infra.refactor._utilities_namespace import *
    from flext_infra.refactor._utilities_pydantic import *
    from flext_infra.refactor._utilities_pydantic_analysis import *
    from flext_infra.refactor.census import *
    from flext_infra.refactor.class_nesting_analyzer import *
    from flext_infra.refactor.cli import *
    from flext_infra.refactor.engine import *
    from flext_infra.refactor.migrate_to_class_mro import *
    from flext_infra.refactor.mro_import_rewriter import *
    from flext_infra.refactor.mro_migration_validator import *
    from flext_infra.refactor.mro_resolver import *
    from flext_infra.refactor.namespace_enforcer import *
    from flext_infra.refactor.project_classifier import *
    from flext_infra.refactor.rule import *
    from flext_infra.refactor.rule_definition_validator import *
    from flext_infra.refactor.safety import *
    from flext_infra.refactor.scanner import *
    from flext_infra.refactor.violation_analyzer import *
    from flext_infra.release import orchestrator
    from flext_infra.release._constants import *
    from flext_infra.release._models import *
    from flext_infra.release.cli import *
    from flext_infra.release.orchestrator import *
    from flext_infra.rules import (
        class_nesting,
        class_reconstructor,
        ensure_future_annotations,
        import_modernizer,
        legacy_removal,
        mro_class_migration,
        pattern_corrections,
    )
    from flext_infra.rules.class_nesting import *
    from flext_infra.rules.class_reconstructor import *
    from flext_infra.rules.ensure_future_annotations import *
    from flext_infra.rules.import_modernizer import *
    from flext_infra.rules.legacy_removal import *
    from flext_infra.rules.mro_class_migration import *
    from flext_infra.rules.pattern_corrections import *
    from flext_infra.transformers import (
        alias_remover,
        census_visitors,
        deprecated_remover,
        dict_to_mapping,
        helper_consolidation,
        import_bypass_remover,
        lazy_import_fixer,
        mro_private_inline,
        mro_remover,
        mro_symbol_propagator,
        nested_class_propagation,
        policy,
        redundant_cast_remover,
        signature_propagator,
        symbol_propagator,
        tier0_import_fixer,
        typing_annotation_replacer,
        typing_unifier,
        violation_census_visitor,
    )
    from flext_infra.transformers._base import *
    from flext_infra.transformers._utilities_normalizer import *
    from flext_infra.transformers.alias_remover import *
    from flext_infra.transformers.census_visitors import *
    from flext_infra.transformers.class_nesting import *
    from flext_infra.transformers.class_reconstructor import *
    from flext_infra.transformers.deprecated_remover import *
    from flext_infra.transformers.dict_to_mapping import *
    from flext_infra.transformers.helper_consolidation import *
    from flext_infra.transformers.import_bypass_remover import *
    from flext_infra.transformers.import_modernizer import *
    from flext_infra.transformers.lazy_import_fixer import *
    from flext_infra.transformers.mro_private_inline import *
    from flext_infra.transformers.mro_remover import *
    from flext_infra.transformers.mro_symbol_propagator import *
    from flext_infra.transformers.nested_class_propagation import *
    from flext_infra.transformers.policy import *
    from flext_infra.transformers.redundant_cast_remover import *
    from flext_infra.transformers.signature_propagator import *
    from flext_infra.transformers.symbol_propagator import *
    from flext_infra.transformers.tier0_import_fixer import *
    from flext_infra.transformers.typing_annotation_replacer import *
    from flext_infra.transformers.typing_unifier import *
    from flext_infra.transformers.violation_census_visitor import *
    from flext_infra.typings import *
    from flext_infra.utilities import *
    from flext_infra.validate import (
        basemk_validator,
        inventory,
        namespace_validator,
        pytest_diag,
        skill_validator,
        stub_chain,
    )
    from flext_infra.validate._constants import *
    from flext_infra.validate._models import *
    from flext_infra.validate.basemk_validator import *
    from flext_infra.validate.cli import *
    from flext_infra.validate.inventory import *
    from flext_infra.validate.namespace_validator import *
    from flext_infra.validate.pytest_diag import *
    from flext_infra.validate.scanner import *
    from flext_infra.validate.skill_validator import *
    from flext_infra.validate.stub_chain import *
    from flext_infra.workspace import (
        maintenance,
        migrator,
        project_makefile,
        sync,
        workspace_makefile,
    )
    from flext_infra.workspace._constants import *
    from flext_infra.workspace._models import *
    from flext_infra.workspace.cli import *
    from flext_infra.workspace.detector import *
    from flext_infra.workspace.maintenance import python_version
    from flext_infra.workspace.maintenance.cli import *
    from flext_infra.workspace.maintenance.python_version import *
    from flext_infra.workspace.migrator import *
    from flext_infra.workspace.orchestrator import *
    from flext_infra.workspace.project_makefile import *
    from flext_infra.workspace.sync import *
    from flext_infra.workspace.workspace_makefile import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "CONTAINER_DICT_SEQ_ADAPTER": "flext_infra.refactor._base_rule",
    "FlextInfraBanditGate": "flext_infra.gates.bandit",
    "FlextInfraBaseMkGenerator": "flext_infra.basemk.generator",
    "FlextInfraBaseMkTemplateEngine": "flext_infra.basemk.engine",
    "FlextInfraBaseMkValidator": "flext_infra.validate.basemk_validator",
    "FlextInfraBasemkConstants": "flext_infra.basemk._constants",
    "FlextInfraBasemkModels": "flext_infra.basemk._models",
    "FlextInfraCensusImportDiscoveryVisitor": "flext_infra.transformers.census_visitors",
    "FlextInfraCensusUsageCollector": "flext_infra.transformers.census_visitors",
    "FlextInfraChangeTracker": "flext_infra.refactor._base_rule",
    "FlextInfraChangeTrackingTransformer": "flext_infra.transformers._base",
    "FlextInfraCheckConstants": "flext_infra.check._constants",
    "FlextInfraCheckModels": "flext_infra.check._models",
    "FlextInfraClassNestingRefactorRule": "flext_infra.rules.class_nesting",
    "FlextInfraClassPlacementDetector": "flext_infra.detectors.class_placement_detector",
    "FlextInfraCli": "flext_infra.cli",
    "FlextInfraCliBasemk": "flext_infra.basemk.cli",
    "FlextInfraCliCheck": "flext_infra.check.cli",
    "FlextInfraCliCodegen": "flext_infra.codegen.cli",
    "FlextInfraCliDeps": "flext_infra.deps.cli",
    "FlextInfraCliDocs": "flext_infra.docs.cli",
    "FlextInfraCliGithub": "flext_infra.github.cli",
    "FlextInfraCliMaintenance": "flext_infra.workspace.maintenance.cli",
    "FlextInfraCliRefactor": "flext_infra.refactor.cli",
    "FlextInfraCliRelease": "flext_infra.release.cli",
    "FlextInfraCliValidate": "flext_infra.validate.cli",
    "FlextInfraCliWorkspace": "flext_infra.workspace.cli",
    "FlextInfraCodegenCensus": "flext_infra.codegen.census",
    "FlextInfraCodegenCoercion": "flext_infra.codegen._codegen_coercion",
    "FlextInfraCodegenConstants": "flext_infra.codegen._constants",
    "FlextInfraCodegenConstantsQualityGate": "flext_infra.codegen.constants_quality_gate",
    "FlextInfraCodegenExecutionTools": "flext_infra.codegen._codegen_execution_tools",
    "FlextInfraCodegenFixer": "flext_infra.codegen.fixer",
    "FlextInfraCodegenGeneration": "flext_infra.codegen._codegen_generation",
    "FlextInfraCodegenLazyInit": "flext_infra.codegen.lazy_init",
    "FlextInfraCodegenMetrics": "flext_infra.codegen._codegen_metrics",
    "FlextInfraCodegenMetricsChecks": "flext_infra.codegen._codegen_metrics_checks",
    "FlextInfraCodegenModels": "flext_infra.codegen._models",
    "FlextInfraCodegenPyTyped": "flext_infra.codegen.py_typed",
    "FlextInfraCodegenScaffolder": "flext_infra.codegen.scaffolder",
    "FlextInfraCodegenSnapshot": "flext_infra.codegen._codegen_snapshot",
    "FlextInfraCompatibilityAliasDetector": "flext_infra.detectors.compatibility_alias_detector",
    "FlextInfraConfigFixer": "flext_infra.check.services",
    "FlextInfraConsolidateGroupsPhase": "flext_infra.deps._phases.consolidate_groups",
    "FlextInfraConstants": "flext_infra.constants",
    "FlextInfraConstantsBase": "flext_infra._constants.base",
    "FlextInfraConstantsCensus": "flext_infra._constants.census",
    "FlextInfraConstantsRope": "flext_infra._constants.rope",
    "FlextInfraCoreConstants": "flext_infra.validate._constants",
    "FlextInfraCoreModels": "flext_infra.validate._models",
    "FlextInfraCyclicImportDetector": "flext_infra.detectors.cyclic_import_detector",
    "FlextInfraDependencyAnalyzer": "flext_infra.detectors.dependency_analyzer_base",
    "FlextInfraDependencyDetectionService": "flext_infra.deps.detection",
    "FlextInfraDependencyDetectorRuntime": "flext_infra.deps._detector_runtime",
    "FlextInfraDependencyPathSync": "flext_infra.deps.path_sync",
    "FlextInfraDepsConstants": "flext_infra.deps._constants",
    "FlextInfraDepsModels": "flext_infra.deps._models",
    "FlextInfraDictToMappingTransformer": "flext_infra.transformers.dict_to_mapping",
    "FlextInfraDocAuditor": "flext_infra.docs.auditor",
    "FlextInfraDocBuilder": "flext_infra.docs.builder",
    "FlextInfraDocFixer": "flext_infra.docs.fixer",
    "FlextInfraDocGenerator": "flext_infra.docs.generator",
    "FlextInfraDocValidator": "flext_infra.docs.validator",
    "FlextInfraDocsCli": "flext_infra.docs.cli",
    "FlextInfraDocsConstants": "flext_infra.docs._constants",
    "FlextInfraDocsModels": "flext_infra.docs._models",
    "FlextInfraEnsureCoverageConfigPhase": "flext_infra.deps._phases.ensure_coverage",
    "FlextInfraEnsureExtraPathsPhase": "flext_infra.deps._phases.ensure_extra_paths",
    "FlextInfraEnsureFormattingToolingPhase": "flext_infra.deps._phases.ensure_formatting",
    "FlextInfraEnsureMypyConfigPhase": "flext_infra.deps._phases.ensure_mypy",
    "FlextInfraEnsureNamespaceToolingPhase": "flext_infra.deps._phases.ensure_namespace",
    "FlextInfraEnsurePydanticMypyConfigPhase": "flext_infra.deps._phases.ensure_pydantic_mypy",
    "FlextInfraEnsurePyreflyConfigPhase": "flext_infra.deps._phases.ensure_pyrefly",
    "FlextInfraEnsurePyrightConfigPhase": "flext_infra.deps._phases.ensure_pyright",
    "FlextInfraEnsurePytestConfigPhase": "flext_infra.deps._phases.ensure_pytest",
    "FlextInfraEnsureRuffConfigPhase": "flext_infra.deps._phases.ensure_ruff",
    "FlextInfraExtraPathsManager": "flext_infra.deps.extra_paths",
    "FlextInfraFunctionDependencyCollector": "flext_infra.refactor._function_dependency_collector",
    "FlextInfraFutureAnnotationsDetector": "flext_infra.detectors.future_annotations_detector",
    "FlextInfraGate": "flext_infra.gates._base_gate",
    "FlextInfraGateRegistry": "flext_infra.gates._gate_registry",
    "FlextInfraGatesModels": "flext_infra.gates._models",
    "FlextInfraGenericTransformerRule": "flext_infra.refactor._base_rule",
    "FlextInfraGithubConstants": "flext_infra.github._constants",
    "FlextInfraGithubModels": "flext_infra.github._models",
    "FlextInfraGoGate": "flext_infra.gates.go",
    "FlextInfraHelperConsolidationTransformer": "flext_infra.transformers.helper_consolidation",
    "FlextInfraImportAliasDetector": "flext_infra.detectors.import_alias_detector",
    "FlextInfraImportCollector": "flext_infra.detectors.import_collector",
    "FlextInfraImportDependencyCollector": "flext_infra.refactor._import_dependency_collector",
    "FlextInfraInjectCommentsPhase": "flext_infra.deps._phases.inject_comments",
    "FlextInfraInternalDependencySyncService": "flext_infra.deps.internal_sync",
    "FlextInfraInternalImportDetector": "flext_infra.detectors.internal_import_detector",
    "FlextInfraInventoryService": "flext_infra.validate.inventory",
    "FlextInfraLooseObjectDetector": "flext_infra.detectors.loose_object_detector",
    "FlextInfraMROCompletenessDetector": "flext_infra.detectors.mro_completeness_detector",
    "FlextInfraManualProtocolDetector": "flext_infra.detectors.manual_protocol_detector",
    "FlextInfraManualTypingAliasDetector": "flext_infra.detectors.manual_typing_alias_detector",
    "FlextInfraMarkdownGate": "flext_infra.gates.markdown",
    "FlextInfraModels": "flext_infra.models",
    "FlextInfraModelsBase": "flext_infra._models.base",
    "FlextInfraModelsCensus": "flext_infra._models.census",
    "FlextInfraModelsCliInputs": "flext_infra._models.cli_inputs",
    "FlextInfraModelsRope": "flext_infra._models.rope",
    "FlextInfraModelsScan": "flext_infra._models.scan",
    "FlextInfraMypyGate": "flext_infra.gates.mypy",
    "FlextInfraNamespaceEnforcer": "flext_infra.refactor.namespace_enforcer",
    "FlextInfraNamespaceEnforcerModels": "flext_infra.refactor._models_namespace_enforcer",
    "FlextInfraNamespaceFacadeScanner": "flext_infra.detectors.namespace_facade_scanner",
    "FlextInfraNamespaceSourceDetector": "flext_infra.detectors.namespace_source_detector",
    "FlextInfraNamespaceValidator": "flext_infra.validate.namespace_validator",
    "FlextInfraNestedClassPropagationTransformer": "flext_infra.transformers.nested_class_propagation",
    "FlextInfraNormalizerContext": "flext_infra.transformers._utilities_normalizer",
    "FlextInfraOrchestratorService": "flext_infra.workspace.orchestrator",
    "FlextInfraPostCheckGate": "flext_infra.refactor._post_check_gate",
    "FlextInfraPreCheckGate": "flext_infra.rules.class_reconstructor",
    "FlextInfraProjectClassifier": "flext_infra.refactor.project_classifier",
    "FlextInfraProjectMakefileUpdater": "flext_infra.workspace.project_makefile",
    "FlextInfraProjectMigrator": "flext_infra.workspace.migrator",
    "FlextInfraProtocols": "flext_infra.protocols",
    "FlextInfraProtocolsBase": "flext_infra._protocols.base",
    "FlextInfraProtocolsRope": "flext_infra._protocols.rope",
    "FlextInfraPyprojectModernizer": "flext_infra.deps.modernizer",
    "FlextInfraPyreflyGate": "flext_infra.gates.pyrefly",
    "FlextInfraPyrightGate": "flext_infra.gates.pyright",
    "FlextInfraPytestDiagExtractor": "flext_infra.validate.pytest_diag",
    "FlextInfraPythonVersionEnforcer": "flext_infra.workspace.maintenance.python_version",
    "FlextInfraRedundantCastRemover": "flext_infra.transformers.redundant_cast_remover",
    "FlextInfraRefactorAliasRemover": "flext_infra.transformers.alias_remover",
    "FlextInfraRefactorAstGrepModels": "flext_infra.refactor._models_ast_grep",
    "FlextInfraRefactorCensus": "flext_infra.refactor.census",
    "FlextInfraRefactorClassNestingAnalyzer": "flext_infra.refactor.class_nesting_analyzer",
    "FlextInfraRefactorClassNestingReconstructor": "flext_infra.rules.class_reconstructor",
    "FlextInfraRefactorClassNestingTransformer": "flext_infra.transformers.class_nesting",
    "FlextInfraRefactorClassReconstructor": "flext_infra.transformers.class_reconstructor",
    "FlextInfraRefactorClassReconstructorRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorConstants": "flext_infra.refactor._constants",
    "FlextInfraRefactorDeprecatedRemover": "flext_infra.transformers.deprecated_remover",
    "FlextInfraRefactorEngine": "flext_infra.refactor.engine",
    "FlextInfraRefactorEnsureFutureAnnotationsRule": "flext_infra.rules.ensure_future_annotations",
    "FlextInfraRefactorImportBypassRemover": "flext_infra.transformers.import_bypass_remover",
    "FlextInfraRefactorImportModernizer": "flext_infra.transformers.import_modernizer",
    "FlextInfraRefactorImportModernizerRule": "flext_infra.rules.import_modernizer",
    "FlextInfraRefactorLazyImportFixer": "flext_infra.transformers.lazy_import_fixer",
    "FlextInfraRefactorLegacyRemovalRule": "flext_infra.rules.legacy_removal",
    "FlextInfraRefactorLooseClassScanner": "flext_infra.refactor.scanner",
    "FlextInfraRefactorMROClassMigrationRule": "flext_infra.rules.mro_class_migration",
    "FlextInfraRefactorMROImportRewriter": "flext_infra.refactor.mro_import_rewriter",
    "FlextInfraRefactorMROMigrationValidator": "flext_infra.refactor.mro_migration_validator",
    "FlextInfraRefactorMROPrivateInlineTransformer": "flext_infra.transformers.mro_private_inline",
    "FlextInfraRefactorMROQualifiedReferenceTransformer": "flext_infra.transformers.mro_private_inline",
    "FlextInfraRefactorMRORedundancyChecker": "flext_infra.refactor.engine",
    "FlextInfraRefactorMRORemover": "flext_infra.transformers.mro_remover",
    "FlextInfraRefactorMROResolver": "flext_infra.refactor.mro_resolver",
    "FlextInfraRefactorMROSymbolPropagator": "flext_infra.transformers.mro_symbol_propagator",
    "FlextInfraRefactorMigrateToClassMRO": "flext_infra.refactor.migrate_to_class_mro",
    "FlextInfraRefactorModels": "flext_infra.refactor._models",
    "FlextInfraRefactorPatternCorrectionsRule": "flext_infra.rules.pattern_corrections",
    "FlextInfraRefactorRule": "flext_infra.refactor._base_rule",
    "FlextInfraRefactorRuleDefinitionValidator": "flext_infra.refactor.rule_definition_validator",
    "FlextInfraRefactorRuleLoader": "flext_infra.refactor.rule",
    "FlextInfraRefactorSafetyManager": "flext_infra.refactor.safety",
    "FlextInfraRefactorSignaturePropagationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorSignaturePropagator": "flext_infra.transformers.signature_propagator",
    "FlextInfraRefactorSymbolPropagationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorSymbolPropagator": "flext_infra.transformers.symbol_propagator",
    "FlextInfraRefactorTier0ImportFixRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTransformerPolicyUtilities": "flext_infra.transformers.policy",
    "FlextInfraRefactorTypingAnnotationFixRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTypingUnificationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTypingUnifier": "flext_infra.transformers.typing_unifier",
    "FlextInfraRefactorViolationAnalyzer": "flext_infra.refactor.violation_analyzer",
    "FlextInfraReleaseConstants": "flext_infra.release._constants",
    "FlextInfraReleaseModels": "flext_infra.release._models",
    "FlextInfraReleaseOrchestrator": "flext_infra.release.orchestrator",
    "FlextInfraRuffFormatGate": "flext_infra.gates.ruff_format",
    "FlextInfraRuffLintGate": "flext_infra.gates.ruff_lint",
    "FlextInfraRuntimeAliasDetector": "flext_infra.detectors.runtime_alias_detector",
    "FlextInfraRuntimeDevDependencyDetector": "flext_infra.deps.detector",
    "FlextInfraScanFileMixin": "flext_infra.detectors._base_detector",
    "FlextInfraSharedInfraConstants": "flext_infra.validate._constants",
    "FlextInfraSkillValidator": "flext_infra.validate.skill_validator",
    "FlextInfraStubSupplyChain": "flext_infra.validate.stub_chain",
    "FlextInfraSyncService": "flext_infra.workspace.sync",
    "FlextInfraTextPatternScanner": "flext_infra.validate.scanner",
    "FlextInfraTopLevelClassCollector": "flext_infra.refactor._top_level_class_collector",
    "FlextInfraTransformerTier0ImportFixer": "flext_infra.transformers.tier0_import_fixer",
    "FlextInfraTypes": "flext_infra.typings",
    "FlextInfraTypesBase": "flext_infra._typings.base",
    "FlextInfraTypesCst": "flext_infra._typings.cst",
    "FlextInfraTypesRope": "flext_infra._typings.rope",
    "FlextInfraTypingAnnotationReplacer": "flext_infra.transformers.typing_annotation_replacer",
    "FlextInfraUtilities": "flext_infra.utilities",
    "FlextInfraUtilitiesBase": "flext_infra._utilities.base",
    "FlextInfraUtilitiesCli": "flext_infra._utilities.cli",
    "FlextInfraUtilitiesCodegen": "flext_infra.codegen._utilities",
    "FlextInfraUtilitiesCodegenAstParsing": "flext_infra.codegen._utilities_codegen_ast_parsing",
    "FlextInfraUtilitiesCodegenConstantDetection": "flext_infra.codegen._utilities_codegen_constant_visitor",
    "FlextInfraUtilitiesCodegenConstantTransformation": "flext_infra.codegen._utilities_codegen_constant_transformer",
    "FlextInfraUtilitiesCodegenExecution": "flext_infra.codegen._utilities_codegen_execution",
    "FlextInfraUtilitiesCodegenGovernance": "flext_infra.codegen._utilities_codegen_governance",
    "FlextInfraUtilitiesCodegenTransforms": "flext_infra.codegen._utilities_transforms",
    "FlextInfraUtilitiesCst": "flext_infra._utilities.cst",
    "FlextInfraUtilitiesDiscovery": "flext_infra._utilities.discovery",
    "FlextInfraUtilitiesDocs": "flext_infra._utilities.docs",
    "FlextInfraUtilitiesFormatting": "flext_infra._utilities.formatting",
    "FlextInfraUtilitiesGit": "flext_infra._utilities.git",
    "FlextInfraUtilitiesGithub": "flext_infra._utilities.github",
    "FlextInfraUtilitiesImportNormalizer": "flext_infra.transformers._utilities_normalizer",
    "FlextInfraUtilitiesIo": "flext_infra._utilities.io",
    "FlextInfraUtilitiesIteration": "flext_infra._utilities.iteration",
    "FlextInfraUtilitiesLogParser": "flext_infra._utilities.log_parser",
    "FlextInfraUtilitiesOutput": "flext_infra._utilities.output",
    "FlextInfraUtilitiesParsing": "flext_infra._utilities.parsing",
    "FlextInfraUtilitiesPaths": "flext_infra._utilities.paths",
    "FlextInfraUtilitiesPatterns": "flext_infra._utilities.patterns",
    "FlextInfraUtilitiesRefactor": "flext_infra.refactor._utilities",
    "FlextInfraUtilitiesRefactorCli": "flext_infra.refactor._utilities_cli",
    "FlextInfraUtilitiesRefactorLoader": "flext_infra.refactor._utilities_loader",
    "FlextInfraUtilitiesRefactorMroScan": "flext_infra.refactor._utilities_mro_scan",
    "FlextInfraUtilitiesRefactorMroTransform": "flext_infra.refactor._utilities_mro_transform",
    "FlextInfraUtilitiesRefactorNamespace": "flext_infra.refactor._utilities_namespace",
    "FlextInfraUtilitiesRefactorPydantic": "flext_infra.refactor._utilities_pydantic",
    "FlextInfraUtilitiesRefactorPydanticAnalysis": "flext_infra.refactor._utilities_pydantic_analysis",
    "FlextInfraUtilitiesRelease": "flext_infra._utilities.release",
    "FlextInfraUtilitiesReporting": "flext_infra._utilities.reporting",
    "FlextInfraUtilitiesRope": "flext_infra._utilities.rope",
    "FlextInfraUtilitiesSafety": "flext_infra._utilities.safety",
    "FlextInfraUtilitiesSelection": "flext_infra._utilities.selection",
    "FlextInfraUtilitiesSubprocess": "flext_infra._utilities.subprocess",
    "FlextInfraUtilitiesTemplates": "flext_infra._utilities.templates",
    "FlextInfraUtilitiesTerminal": "flext_infra._utilities.terminal",
    "FlextInfraUtilitiesToml": "flext_infra._utilities.toml",
    "FlextInfraUtilitiesTomlParse": "flext_infra._utilities.toml_parse",
    "FlextInfraUtilitiesVersioning": "flext_infra._utilities.versioning",
    "FlextInfraUtilitiesYaml": "flext_infra._utilities.yaml",
    "FlextInfraViolationCensusVisitor": "flext_infra.transformers.violation_census_visitor",
    "FlextInfraWorkspaceChecker": "flext_infra.check.services",
    "FlextInfraWorkspaceConstants": "flext_infra.workspace._constants",
    "FlextInfraWorkspaceDetector": "flext_infra.workspace.detector",
    "FlextInfraWorkspaceMakefileGenerator": "flext_infra.workspace.workspace_makefile",
    "FlextInfraWorkspaceMode": "flext_infra.workspace.detector",
    "FlextInfraWorkspaceModels": "flext_infra.workspace._models",
    "INFRA_MAPPING_ADAPTER": "flext_infra.refactor._base_rule",
    "INFRA_SEQ_ADAPTER": "flext_infra.refactor._base_rule",
    "STR_MAPPING_ADAPTER": "flext_infra.refactor._base_rule",
    "_DetectorContext": "flext_infra.detectors._base_detector",
    "_constants": "flext_infra._constants",
    "_models": "flext_infra._models",
    "_protocols": "flext_infra._protocols",
    "_typings": "flext_infra._typings",
    "_utilities": "flext_infra._utilities",
    "alias_remover": "flext_infra.transformers.alias_remover",
    "auditor": "flext_infra.docs.auditor",
    "bandit": "flext_infra.gates.bandit",
    "base": "flext_infra._constants.base",
    "basemk": "flext_infra.basemk",
    "basemk_validator": "flext_infra.validate.basemk_validator",
    "build_parser": "flext_infra.check.workspace_check",
    "builder": "flext_infra.docs.builder",
    "c": ["flext_infra.constants", "FlextInfraConstants"],
    "census": "flext_infra._constants.census",
    "census_visitors": "flext_infra.transformers.census_visitors",
    "check": "flext_infra.check",
    "class_nesting": "flext_infra.rules.class_nesting",
    "class_nesting_analyzer": "flext_infra.refactor.class_nesting_analyzer",
    "class_placement_detector": "flext_infra.detectors.class_placement_detector",
    "class_reconstructor": "flext_infra.rules.class_reconstructor",
    "cli": "flext_infra.cli",
    "cli_inputs": "flext_infra._models.cli_inputs",
    "codegen": "flext_infra.codegen",
    "compatibility_alias_detector": "flext_infra.detectors.compatibility_alias_detector",
    "consolidate_groups": "flext_infra.deps._phases.consolidate_groups",
    "constants": "flext_infra.constants",
    "constants_quality_gate": "flext_infra.codegen.constants_quality_gate",
    "cst": "flext_infra._typings.cst",
    "cyclic_import_detector": "flext_infra.detectors.cyclic_import_detector",
    "d": "flext_cli",
    "dependency_analyzer_base": "flext_infra.detectors.dependency_analyzer_base",
    "deprecated_remover": "flext_infra.transformers.deprecated_remover",
    "deps": "flext_infra.deps",
    "detection": "flext_infra.deps.detection",
    "detector": "flext_infra.deps.detector",
    "detectors": "flext_infra.detectors",
    "dict_to_mapping": "flext_infra.transformers.dict_to_mapping",
    "discovery": "flext_infra._utilities.discovery",
    "docs": "flext_infra._utilities.docs",
    "e": "flext_cli",
    "engine": "flext_infra.basemk.engine",
    "ensure_coverage": "flext_infra.deps._phases.ensure_coverage",
    "ensure_extra_paths": "flext_infra.deps._phases.ensure_extra_paths",
    "ensure_formatting": "flext_infra.deps._phases.ensure_formatting",
    "ensure_future_annotations": "flext_infra.rules.ensure_future_annotations",
    "ensure_mypy": "flext_infra.deps._phases.ensure_mypy",
    "ensure_namespace": "flext_infra.deps._phases.ensure_namespace",
    "ensure_pydantic_mypy": "flext_infra.deps._phases.ensure_pydantic_mypy",
    "ensure_pyrefly": "flext_infra.deps._phases.ensure_pyrefly",
    "ensure_pyright": "flext_infra.deps._phases.ensure_pyright",
    "ensure_pytest": "flext_infra.deps._phases.ensure_pytest",
    "ensure_ruff": "flext_infra.deps._phases.ensure_ruff",
    "extra_paths": "flext_infra.deps.extra_paths",
    "fix_pyrefly_config": "flext_infra.deps.fix_pyrefly_config",
    "fixer": "flext_infra.codegen.fixer",
    "formatting": "flext_infra._utilities.formatting",
    "future_annotations_detector": "flext_infra.detectors.future_annotations_detector",
    "gates": "flext_infra.gates",
    "generator": "flext_infra.basemk.generator",
    "git": "flext_infra._utilities.git",
    "github": "flext_infra._utilities.github",
    "go": "flext_infra.gates.go",
    "h": "flext_cli",
    "helper_consolidation": "flext_infra.transformers.helper_consolidation",
    "import_alias_detector": "flext_infra.detectors.import_alias_detector",
    "import_bypass_remover": "flext_infra.transformers.import_bypass_remover",
    "import_collector": "flext_infra.detectors.import_collector",
    "import_modernizer": "flext_infra.rules.import_modernizer",
    "inject_comments": "flext_infra.deps._phases.inject_comments",
    "internal_import_detector": "flext_infra.detectors.internal_import_detector",
    "internal_sync": "flext_infra.deps.internal_sync",
    "inventory": "flext_infra.validate.inventory",
    "io": "flext_infra._utilities.io",
    "iteration": "flext_infra._utilities.iteration",
    "lazy_import_fixer": "flext_infra.transformers.lazy_import_fixer",
    "lazy_init": "flext_infra.codegen.lazy_init",
    "legacy_removal": "flext_infra.rules.legacy_removal",
    "log_parser": "flext_infra._utilities.log_parser",
    "logger": "flext_infra.workspace.maintenance.python_version",
    "loose_object_detector": "flext_infra.detectors.loose_object_detector",
    "m": ["flext_infra.models", "FlextInfraModels"],
    "main": "flext_infra.cli",
    "maintenance": "flext_infra.workspace.maintenance",
    "manual_protocol_detector": "flext_infra.detectors.manual_protocol_detector",
    "manual_typing_alias_detector": "flext_infra.detectors.manual_typing_alias_detector",
    "markdown": "flext_infra.gates.markdown",
    "migrate_to_class_mro": "flext_infra.refactor.migrate_to_class_mro",
    "migrator": "flext_infra.workspace.migrator",
    "models": "flext_infra.models",
    "modernizer": "flext_infra.deps.modernizer",
    "mro_class_migration": "flext_infra.rules.mro_class_migration",
    "mro_completeness_detector": "flext_infra.detectors.mro_completeness_detector",
    "mro_import_rewriter": "flext_infra.refactor.mro_import_rewriter",
    "mro_migration_validator": "flext_infra.refactor.mro_migration_validator",
    "mro_private_inline": "flext_infra.transformers.mro_private_inline",
    "mro_remover": "flext_infra.transformers.mro_remover",
    "mro_resolver": "flext_infra.refactor.mro_resolver",
    "mro_symbol_propagator": "flext_infra.transformers.mro_symbol_propagator",
    "mypy": "flext_infra.gates.mypy",
    "namespace_enforcer": "flext_infra.refactor.namespace_enforcer",
    "namespace_facade_scanner": "flext_infra.detectors.namespace_facade_scanner",
    "namespace_source_detector": "flext_infra.detectors.namespace_source_detector",
    "namespace_validator": "flext_infra.validate.namespace_validator",
    "nested_class_propagation": "flext_infra.transformers.nested_class_propagation",
    "orchestrator": "flext_infra.release.orchestrator",
    "output": "flext_infra._utilities.output",
    "p": ["flext_infra.protocols", "FlextInfraProtocols"],
    "parsing": "flext_infra._utilities.parsing",
    "path_sync": "flext_infra.deps.path_sync",
    "paths": "flext_infra._utilities.paths",
    "pattern_corrections": "flext_infra.rules.pattern_corrections",
    "patterns": "flext_infra._utilities.patterns",
    "policy": "flext_infra.transformers.policy",
    "project_classifier": "flext_infra.refactor.project_classifier",
    "project_makefile": "flext_infra.workspace.project_makefile",
    "protocols": "flext_infra.protocols",
    "py_typed": "flext_infra.codegen.py_typed",
    "pyrefly": "flext_infra.gates.pyrefly",
    "pyright": "flext_infra.gates.pyright",
    "pytest_diag": "flext_infra.validate.pytest_diag",
    "python_version": "flext_infra.workspace.maintenance.python_version",
    "r": "flext_cli",
    "redundant_cast_remover": "flext_infra.transformers.redundant_cast_remover",
    "refactor": "flext_infra.refactor",
    "release": "flext_infra._utilities.release",
    "reporting": "flext_infra._utilities.reporting",
    "rope": "flext_infra._constants.rope",
    "ruff_format": "flext_infra.gates.ruff_format",
    "ruff_lint": "flext_infra.gates.ruff_lint",
    "rule": "flext_infra.refactor.rule",
    "rule_definition_validator": "flext_infra.refactor.rule_definition_validator",
    "rules": "flext_infra.rules",
    "run_cli": "flext_infra.check.workspace_check",
    "runtime_alias_detector": "flext_infra.detectors.runtime_alias_detector",
    "s": "flext_cli",
    "safety": "flext_infra._utilities.safety",
    "scaffolder": "flext_infra.codegen.scaffolder",
    "scan": "flext_infra._models.scan",
    "scanner": "flext_infra.refactor.scanner",
    "selection": "flext_infra._utilities.selection",
    "services": "flext_infra.check.services",
    "signature_propagator": "flext_infra.transformers.signature_propagator",
    "skill_validator": "flext_infra.validate.skill_validator",
    "stub_chain": "flext_infra.validate.stub_chain",
    "subprocess": "flext_infra._utilities.subprocess",
    "symbol_propagator": "flext_infra.transformers.symbol_propagator",
    "sync": "flext_infra.workspace.sync",
    "t": ["flext_infra.typings", "FlextInfraTypes"],
    "templates": "flext_infra._utilities.templates",
    "terminal": "flext_infra._utilities.terminal",
    "tier0_import_fixer": "flext_infra.transformers.tier0_import_fixer",
    "toml": "flext_infra._utilities.toml",
    "toml_parse": "flext_infra._utilities.toml_parse",
    "transformers": "flext_infra.transformers",
    "typing_annotation_replacer": "flext_infra.transformers.typing_annotation_replacer",
    "typing_unifier": "flext_infra.transformers.typing_unifier",
    "typings": "flext_infra.typings",
    "u": ["flext_infra.utilities", "FlextInfraUtilities"],
    "utilities": "flext_infra.utilities",
    "validate": "flext_infra.validate",
    "validator": "flext_infra.docs.validator",
    "versioning": "flext_infra._utilities.versioning",
    "violation_analyzer": "flext_infra.refactor.violation_analyzer",
    "violation_census_visitor": "flext_infra.transformers.violation_census_visitor",
    "workspace": "flext_infra.workspace",
    "workspace_check": "flext_infra.check.workspace_check",
    "workspace_makefile": "flext_infra.workspace.workspace_makefile",
    "x": "flext_cli",
    "yaml": "flext_infra._utilities.yaml",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
