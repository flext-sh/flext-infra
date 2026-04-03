# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.refactor._base_rule as _flext_infra_refactor__base_rule

    _base_rule = _flext_infra_refactor__base_rule
    import flext_infra.refactor._constants as _flext_infra_refactor__constants
    from flext_infra.refactor._base_rule import (
        CONTAINER_DICT_SEQ_ADAPTER,
        INFRA_MAPPING_ADAPTER,
        INFRA_SEQ_ADAPTER,
        STR_MAPPING_ADAPTER,
        FlextInfraChangeTracker,
        FlextInfraGenericTransformerRule,
        FlextInfraRefactorRule,
    )

    _constants = _flext_infra_refactor__constants
    import flext_infra.refactor._engine_orchestration as _flext_infra_refactor__engine_orchestration
    from flext_infra.refactor._constants import FlextInfraRefactorConstants

    _engine_orchestration = _flext_infra_refactor__engine_orchestration
    import flext_infra.refactor._engine_pipeline as _flext_infra_refactor__engine_pipeline
    from flext_infra.refactor._engine_orchestration import (
        FlextInfraRefactorEngineOrchestrationMixin,
    )

    _engine_pipeline = _flext_infra_refactor__engine_pipeline
    import flext_infra.refactor._engine_rules as _flext_infra_refactor__engine_rules
    from flext_infra.refactor._engine_pipeline import (
        FlextInfraRefactorEnginePipelineMixin,
    )

    _engine_rules = _flext_infra_refactor__engine_rules
    import flext_infra.refactor._models as _flext_infra_refactor__models
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

    _models = _flext_infra_refactor__models
    import flext_infra.refactor._models_ast_grep as _flext_infra_refactor__models_ast_grep
    from flext_infra.refactor._models import FlextInfraRefactorModels

    _models_ast_grep = _flext_infra_refactor__models_ast_grep
    import flext_infra.refactor._models_census as _flext_infra_refactor__models_census
    from flext_infra.refactor._models_ast_grep import FlextInfraRefactorAstGrepModels

    _models_census = _flext_infra_refactor__models_census
    import flext_infra.refactor._models_namespace_enforcer as _flext_infra_refactor__models_namespace_enforcer
    from flext_infra.refactor._models_census import FlextInfraRefactorModelsCensus

    _models_namespace_enforcer = _flext_infra_refactor__models_namespace_enforcer
    import flext_infra.refactor._models_violations as _flext_infra_refactor__models_violations
    from flext_infra.refactor._models_namespace_enforcer import (
        FlextInfraNamespaceEnforcerModels,
    )

    _models_violations = _flext_infra_refactor__models_violations
    import flext_infra.refactor._namespace_enforcer_phases as _flext_infra_refactor__namespace_enforcer_phases
    from flext_infra.refactor._models_violations import (
        FlextInfraRefactorModelsViolations,
    )

    _namespace_enforcer_phases = _flext_infra_refactor__namespace_enforcer_phases
    import flext_infra.refactor._post_check_gate as _flext_infra_refactor__post_check_gate
    from flext_infra.refactor._namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin,
    )

    _post_check_gate = _flext_infra_refactor__post_check_gate
    import flext_infra.refactor._utilities as _flext_infra_refactor__utilities
    from flext_infra.refactor._post_check_gate import FlextInfraPostCheckGate

    _utilities = _flext_infra_refactor__utilities
    import flext_infra.refactor._utilities_census as _flext_infra_refactor__utilities_census
    from flext_infra.refactor._utilities import FlextInfraUtilitiesRefactor

    _utilities_census = _flext_infra_refactor__utilities_census
    import flext_infra.refactor._utilities_cli as _flext_infra_refactor__utilities_cli
    from flext_infra.refactor._utilities_census import FlextInfraUtilitiesRefactorCensus

    _utilities_cli = _flext_infra_refactor__utilities_cli
    import flext_infra.refactor._utilities_engine as _flext_infra_refactor__utilities_engine
    from flext_infra.refactor._utilities_cli import FlextInfraUtilitiesRefactorCli

    _utilities_engine = _flext_infra_refactor__utilities_engine
    import flext_infra.refactor._utilities_loader as _flext_infra_refactor__utilities_loader
    from flext_infra.refactor._utilities_engine import FlextInfraUtilitiesRefactorEngine

    _utilities_loader = _flext_infra_refactor__utilities_loader
    import flext_infra.refactor._utilities_mro_scan as _flext_infra_refactor__utilities_mro_scan
    from flext_infra.refactor._utilities_loader import FlextInfraUtilitiesRefactorLoader

    _utilities_mro_scan = _flext_infra_refactor__utilities_mro_scan
    import flext_infra.refactor._utilities_mro_transform as _flext_infra_refactor__utilities_mro_transform
    from flext_infra.refactor._utilities_mro_scan import (
        FlextInfraUtilitiesRefactorMroScan,
    )

    _utilities_mro_transform = _flext_infra_refactor__utilities_mro_transform
    import flext_infra.refactor._utilities_namespace as _flext_infra_refactor__utilities_namespace
    from flext_infra.refactor._utilities_mro_transform import (
        FlextInfraUtilitiesRefactorMroTransform,
    )

    _utilities_namespace = _flext_infra_refactor__utilities_namespace
    import flext_infra.refactor._utilities_namespace_common as _flext_infra_refactor__utilities_namespace_common
    from flext_infra.refactor._utilities_namespace import (
        FlextInfraUtilitiesRefactorNamespace,
    )

    _utilities_namespace_common = _flext_infra_refactor__utilities_namespace_common
    import flext_infra.refactor._utilities_namespace_facades as _flext_infra_refactor__utilities_namespace_facades
    from flext_infra.refactor._utilities_namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
    )

    _utilities_namespace_facades = _flext_infra_refactor__utilities_namespace_facades
    import flext_infra.refactor._utilities_namespace_moves as _flext_infra_refactor__utilities_namespace_moves
    from flext_infra.refactor._utilities_namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades,
    )

    _utilities_namespace_moves = _flext_infra_refactor__utilities_namespace_moves
    import flext_infra.refactor._utilities_namespace_mro as _flext_infra_refactor__utilities_namespace_mro
    from flext_infra.refactor._utilities_namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )

    _utilities_namespace_mro = _flext_infra_refactor__utilities_namespace_mro
    import flext_infra.refactor._utilities_namespace_runtime as _flext_infra_refactor__utilities_namespace_runtime
    from flext_infra.refactor._utilities_namespace_mro import (
        FlextInfraUtilitiesRefactorNamespaceMro,
    )

    _utilities_namespace_runtime = _flext_infra_refactor__utilities_namespace_runtime
    import flext_infra.refactor._utilities_policy as _flext_infra_refactor__utilities_policy
    from flext_infra.refactor._utilities_namespace_runtime import (
        FlextInfraUtilitiesRefactorNamespaceRuntime,
    )

    _utilities_policy = _flext_infra_refactor__utilities_policy
    import flext_infra.refactor._utilities_pydantic as _flext_infra_refactor__utilities_pydantic
    from flext_infra.refactor._utilities_policy import FlextInfraUtilitiesRefactorPolicy

    _utilities_pydantic = _flext_infra_refactor__utilities_pydantic
    import flext_infra.refactor._utilities_pydantic_analysis as _flext_infra_refactor__utilities_pydantic_analysis
    from flext_infra.refactor._utilities_pydantic import (
        FlextInfraUtilitiesRefactorPydantic,
    )

    _utilities_pydantic_analysis = _flext_infra_refactor__utilities_pydantic_analysis
    import flext_infra.refactor.census as _flext_infra_refactor_census
    from flext_infra.refactor._utilities_pydantic_analysis import (
        FlextInfraUtilitiesRefactorPydanticAnalysis,
    )

    census = _flext_infra_refactor_census
    import flext_infra.refactor.class_nesting_analyzer as _flext_infra_refactor_class_nesting_analyzer
    from flext_infra.refactor.census import FlextInfraRefactorCensus

    class_nesting_analyzer = _flext_infra_refactor_class_nesting_analyzer
    import flext_infra.refactor.cli as _flext_infra_refactor_cli
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer,
    )

    cli = _flext_infra_refactor_cli
    import flext_infra.refactor.engine as _flext_infra_refactor_engine
    from flext_infra.refactor.cli import FlextInfraCliRefactor

    engine = _flext_infra_refactor_engine
    import flext_infra.refactor.migrate_to_class_mro as _flext_infra_refactor_migrate_to_class_mro
    from flext_infra.refactor.engine import FlextInfraRefactorEngine

    migrate_to_class_mro = _flext_infra_refactor_migrate_to_class_mro
    import flext_infra.refactor.mro_import_rewriter as _flext_infra_refactor_mro_import_rewriter
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO,
    )

    mro_import_rewriter = _flext_infra_refactor_mro_import_rewriter
    import flext_infra.refactor.mro_migration_validator as _flext_infra_refactor_mro_migration_validator
    from flext_infra.refactor.mro_import_rewriter import (
        FlextInfraRefactorMROImportRewriter,
    )

    mro_migration_validator = _flext_infra_refactor_mro_migration_validator
    import flext_infra.refactor.mro_resolver as _flext_infra_refactor_mro_resolver
    from flext_infra.refactor.mro_migration_validator import (
        FlextInfraRefactorMROMigrationValidator,
    )

    mro_resolver = _flext_infra_refactor_mro_resolver
    import flext_infra.refactor.namespace_enforcer as _flext_infra_refactor_namespace_enforcer
    from flext_infra.refactor.mro_resolver import FlextInfraRefactorMROResolver

    namespace_enforcer = _flext_infra_refactor_namespace_enforcer
    import flext_infra.refactor.project_classifier as _flext_infra_refactor_project_classifier
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer

    project_classifier = _flext_infra_refactor_project_classifier
    import flext_infra.refactor.rule as _flext_infra_refactor_rule
    from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier

    rule = _flext_infra_refactor_rule
    import flext_infra.refactor.rule_definition_validator as _flext_infra_refactor_rule_definition_validator
    from flext_infra.refactor.rule import FlextInfraRefactorRuleLoader

    rule_definition_validator = _flext_infra_refactor_rule_definition_validator
    import flext_infra.refactor.safety as _flext_infra_refactor_safety
    from flext_infra.refactor.rule_definition_validator import (
        FlextInfraRefactorRuleDefinitionValidator,
    )

    safety = _flext_infra_refactor_safety
    import flext_infra.refactor.scanner as _flext_infra_refactor_scanner
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager

    scanner = _flext_infra_refactor_scanner
    import flext_infra.refactor.violation_analyzer as _flext_infra_refactor_violation_analyzer
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner

    violation_analyzer = _flext_infra_refactor_violation_analyzer
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )
_LAZY_IMPORTS = {
    "CONTAINER_DICT_SEQ_ADAPTER": "flext_infra.refactor._base_rule",
    "FlextInfraChangeTracker": "flext_infra.refactor._base_rule",
    "FlextInfraCliRefactor": "flext_infra.refactor.cli",
    "FlextInfraGenericTransformerRule": "flext_infra.refactor._base_rule",
    "FlextInfraNamespaceEnforcer": "flext_infra.refactor.namespace_enforcer",
    "FlextInfraNamespaceEnforcerModels": "flext_infra.refactor._models_namespace_enforcer",
    "FlextInfraNamespaceEnforcerPhasesMixin": "flext_infra.refactor._namespace_enforcer_phases",
    "FlextInfraPostCheckGate": "flext_infra.refactor._post_check_gate",
    "FlextInfraProjectClassifier": "flext_infra.refactor.project_classifier",
    "FlextInfraRefactorAstGrepModels": "flext_infra.refactor._models_ast_grep",
    "FlextInfraRefactorCensus": "flext_infra.refactor.census",
    "FlextInfraRefactorClassNestingAnalyzer": "flext_infra.refactor.class_nesting_analyzer",
    "FlextInfraRefactorClassReconstructorRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorConstants": "flext_infra.refactor._constants",
    "FlextInfraRefactorEngine": "flext_infra.refactor.engine",
    "FlextInfraRefactorEngineOrchestrationMixin": "flext_infra.refactor._engine_orchestration",
    "FlextInfraRefactorEnginePipelineMixin": "flext_infra.refactor._engine_pipeline",
    "FlextInfraRefactorLegacyRemovalTextRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorLooseClassScanner": "flext_infra.refactor.scanner",
    "FlextInfraRefactorMROClassMigrationTextRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorMROImportRewriter": "flext_infra.refactor.mro_import_rewriter",
    "FlextInfraRefactorMROMigrationValidator": "flext_infra.refactor.mro_migration_validator",
    "FlextInfraRefactorMRORedundancyChecker": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorMROResolver": "flext_infra.refactor.mro_resolver",
    "FlextInfraRefactorMigrateToClassMRO": "flext_infra.refactor.migrate_to_class_mro",
    "FlextInfraRefactorModels": "flext_infra.refactor._models",
    "FlextInfraRefactorModelsCensus": "flext_infra.refactor._models_census",
    "FlextInfraRefactorModelsViolations": "flext_infra.refactor._models_violations",
    "FlextInfraRefactorPatternCorrectionsTextRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorRule": "flext_infra.refactor._base_rule",
    "FlextInfraRefactorRuleDefinitionValidator": "flext_infra.refactor.rule_definition_validator",
    "FlextInfraRefactorRuleLoader": "flext_infra.refactor.rule",
    "FlextInfraRefactorSafetyManager": "flext_infra.refactor.safety",
    "FlextInfraRefactorSignaturePropagationRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorSymbolPropagationRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorTier0ImportFixRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorTypingAnnotationFixRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorTypingUnificationRule": "flext_infra.refactor._engine_rules",
    "FlextInfraRefactorViolationAnalyzer": "flext_infra.refactor.violation_analyzer",
    "FlextInfraUtilitiesRefactor": "flext_infra.refactor._utilities",
    "FlextInfraUtilitiesRefactorCensus": "flext_infra.refactor._utilities_census",
    "FlextInfraUtilitiesRefactorCli": "flext_infra.refactor._utilities_cli",
    "FlextInfraUtilitiesRefactorEngine": "flext_infra.refactor._utilities_engine",
    "FlextInfraUtilitiesRefactorLoader": "flext_infra.refactor._utilities_loader",
    "FlextInfraUtilitiesRefactorMroScan": "flext_infra.refactor._utilities_mro_scan",
    "FlextInfraUtilitiesRefactorMroTransform": "flext_infra.refactor._utilities_mro_transform",
    "FlextInfraUtilitiesRefactorNamespace": "flext_infra.refactor._utilities_namespace",
    "FlextInfraUtilitiesRefactorNamespaceCommon": "flext_infra.refactor._utilities_namespace_common",
    "FlextInfraUtilitiesRefactorNamespaceFacades": "flext_infra.refactor._utilities_namespace_facades",
    "FlextInfraUtilitiesRefactorNamespaceMoves": "flext_infra.refactor._utilities_namespace_moves",
    "FlextInfraUtilitiesRefactorNamespaceMro": "flext_infra.refactor._utilities_namespace_mro",
    "FlextInfraUtilitiesRefactorNamespaceRuntime": "flext_infra.refactor._utilities_namespace_runtime",
    "FlextInfraUtilitiesRefactorPolicy": "flext_infra.refactor._utilities_policy",
    "FlextInfraUtilitiesRefactorPydantic": "flext_infra.refactor._utilities_pydantic",
    "FlextInfraUtilitiesRefactorPydanticAnalysis": "flext_infra.refactor._utilities_pydantic_analysis",
    "INFRA_MAPPING_ADAPTER": "flext_infra.refactor._base_rule",
    "INFRA_SEQ_ADAPTER": "flext_infra.refactor._base_rule",
    "STR_MAPPING_ADAPTER": "flext_infra.refactor._base_rule",
    "_base_rule": "flext_infra.refactor._base_rule",
    "_constants": "flext_infra.refactor._constants",
    "_engine_orchestration": "flext_infra.refactor._engine_orchestration",
    "_engine_pipeline": "flext_infra.refactor._engine_pipeline",
    "_engine_rules": "flext_infra.refactor._engine_rules",
    "_models": "flext_infra.refactor._models",
    "_models_ast_grep": "flext_infra.refactor._models_ast_grep",
    "_models_census": "flext_infra.refactor._models_census",
    "_models_namespace_enforcer": "flext_infra.refactor._models_namespace_enforcer",
    "_models_violations": "flext_infra.refactor._models_violations",
    "_namespace_enforcer_phases": "flext_infra.refactor._namespace_enforcer_phases",
    "_post_check_gate": "flext_infra.refactor._post_check_gate",
    "_utilities": "flext_infra.refactor._utilities",
    "_utilities_census": "flext_infra.refactor._utilities_census",
    "_utilities_cli": "flext_infra.refactor._utilities_cli",
    "_utilities_engine": "flext_infra.refactor._utilities_engine",
    "_utilities_loader": "flext_infra.refactor._utilities_loader",
    "_utilities_mro_scan": "flext_infra.refactor._utilities_mro_scan",
    "_utilities_mro_transform": "flext_infra.refactor._utilities_mro_transform",
    "_utilities_namespace": "flext_infra.refactor._utilities_namespace",
    "_utilities_namespace_common": "flext_infra.refactor._utilities_namespace_common",
    "_utilities_namespace_facades": "flext_infra.refactor._utilities_namespace_facades",
    "_utilities_namespace_moves": "flext_infra.refactor._utilities_namespace_moves",
    "_utilities_namespace_mro": "flext_infra.refactor._utilities_namespace_mro",
    "_utilities_namespace_runtime": "flext_infra.refactor._utilities_namespace_runtime",
    "_utilities_policy": "flext_infra.refactor._utilities_policy",
    "_utilities_pydantic": "flext_infra.refactor._utilities_pydantic",
    "_utilities_pydantic_analysis": "flext_infra.refactor._utilities_pydantic_analysis",
    "c": ("flext_core.constants", "FlextConstants"),
    "census": "flext_infra.refactor.census",
    "class_nesting_analyzer": "flext_infra.refactor.class_nesting_analyzer",
    "cli": "flext_infra.refactor.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "engine": "flext_infra.refactor.engine",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "migrate_to_class_mro": "flext_infra.refactor.migrate_to_class_mro",
    "mro_import_rewriter": "flext_infra.refactor.mro_import_rewriter",
    "mro_migration_validator": "flext_infra.refactor.mro_migration_validator",
    "mro_resolver": "flext_infra.refactor.mro_resolver",
    "namespace_enforcer": "flext_infra.refactor.namespace_enforcer",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "project_classifier": "flext_infra.refactor.project_classifier",
    "r": ("flext_core.result", "FlextResult"),
    "rule": "flext_infra.refactor.rule",
    "rule_definition_validator": "flext_infra.refactor.rule_definition_validator",
    "s": ("flext_core.service", "FlextService"),
    "safety": "flext_infra.refactor.safety",
    "scanner": "flext_infra.refactor.scanner",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "violation_analyzer": "flext_infra.refactor.violation_analyzer",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "CONTAINER_DICT_SEQ_ADAPTER",
    "INFRA_MAPPING_ADAPTER",
    "INFRA_SEQ_ADAPTER",
    "STR_MAPPING_ADAPTER",
    "FlextInfraChangeTracker",
    "FlextInfraCliRefactor",
    "FlextInfraGenericTransformerRule",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerModels",
    "FlextInfraNamespaceEnforcerPhasesMixin",
    "FlextInfraPostCheckGate",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorAstGrepModels",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorConstants",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorEngineOrchestrationMixin",
    "FlextInfraRefactorEnginePipelineMixin",
    "FlextInfraRefactorLegacyRemovalTextRule",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROClassMigrationTextRule",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorModels",
    "FlextInfraRefactorModelsCensus",
    "FlextInfraRefactorModelsViolations",
    "FlextInfraRefactorPatternCorrectionsTextRule",
    "FlextInfraRefactorRule",
    "FlextInfraRefactorRuleDefinitionValidator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorTier0ImportFixRule",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
    "FlextInfraRefactorViolationAnalyzer",
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
    "_base_rule",
    "_constants",
    "_engine_orchestration",
    "_engine_pipeline",
    "_engine_rules",
    "_models",
    "_models_ast_grep",
    "_models_census",
    "_models_namespace_enforcer",
    "_models_violations",
    "_namespace_enforcer_phases",
    "_post_check_gate",
    "_utilities",
    "_utilities_census",
    "_utilities_cli",
    "_utilities_engine",
    "_utilities_loader",
    "_utilities_mro_scan",
    "_utilities_mro_transform",
    "_utilities_namespace",
    "_utilities_namespace_common",
    "_utilities_namespace_facades",
    "_utilities_namespace_moves",
    "_utilities_namespace_mro",
    "_utilities_namespace_runtime",
    "_utilities_policy",
    "_utilities_pydantic",
    "_utilities_pydantic_analysis",
    "c",
    "census",
    "class_nesting_analyzer",
    "cli",
    "d",
    "e",
    "engine",
    "h",
    "m",
    "migrate_to_class_mro",
    "mro_import_rewriter",
    "mro_migration_validator",
    "mro_resolver",
    "namespace_enforcer",
    "p",
    "project_classifier",
    "r",
    "rule",
    "rule_definition_validator",
    "s",
    "safety",
    "scanner",
    "t",
    "u",
    "violation_analyzer",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
