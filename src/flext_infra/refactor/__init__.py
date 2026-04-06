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
    import flext_infra.refactor._engine_helpers as _flext_infra_refactor__engine_helpers
    from flext_infra.refactor._base_rule import (
        FlextInfraGenericTransformerRule,
        FlextInfraRefactorRule,
    )

    _engine_helpers = _flext_infra_refactor__engine_helpers
    import flext_infra.refactor._engine_rules as _flext_infra_refactor__engine_rules
    from flext_infra.refactor._engine_helpers import (
        FlextInfraRefactorEngineHelpersMixin,
    )

    _engine_rules = _flext_infra_refactor__engine_rules
    import flext_infra.refactor._namespace_enforcer_phases as _flext_infra_refactor__namespace_enforcer_phases
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

    _namespace_enforcer_phases = _flext_infra_refactor__namespace_enforcer_phases
    import flext_infra.refactor._utilities as _flext_infra_refactor__utilities
    from flext_infra.refactor._namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin,
    )

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
    import flext_infra.refactor._utilities_mro_scan as _flext_infra_refactor__utilities_mro_scan
    from flext_infra.refactor._utilities_engine import FlextInfraUtilitiesRefactorEngine

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
    import flext_infra.refactor._utilities_namespace_analysis as _flext_infra_refactor__utilities_namespace_analysis
    from flext_infra.refactor._utilities_namespace import (
        FlextInfraUtilitiesRefactorNamespace,
    )

    _utilities_namespace_analysis = _flext_infra_refactor__utilities_namespace_analysis
    import flext_infra.refactor._utilities_namespace_facades as _flext_infra_refactor__utilities_namespace_facades
    from flext_infra.refactor._utilities_namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceMro,
    )

    _utilities_namespace_facades = _flext_infra_refactor__utilities_namespace_facades
    import flext_infra.refactor._utilities_namespace_moves as _flext_infra_refactor__utilities_namespace_moves
    from flext_infra.refactor._utilities_namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades,
    )

    _utilities_namespace_moves = _flext_infra_refactor__utilities_namespace_moves
    import flext_infra.refactor._utilities_namespace_runtime as _flext_infra_refactor__utilities_namespace_runtime
    from flext_infra.refactor._utilities_namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
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
    "FlextInfraCliRefactor": ("flext_infra.refactor.cli", "FlextInfraCliRefactor"),
    "FlextInfraGenericTransformerRule": (
        "flext_infra.refactor._base_rule",
        "FlextInfraGenericTransformerRule",
    ),
    "FlextInfraNamespaceEnforcer": (
        "flext_infra.refactor.namespace_enforcer",
        "FlextInfraNamespaceEnforcer",
    ),
    "FlextInfraNamespaceEnforcerPhasesMixin": (
        "flext_infra.refactor._namespace_enforcer_phases",
        "FlextInfraNamespaceEnforcerPhasesMixin",
    ),
    "FlextInfraProjectClassifier": (
        "flext_infra.refactor.project_classifier",
        "FlextInfraProjectClassifier",
    ),
    "FlextInfraRefactorCensus": (
        "flext_infra.refactor.census",
        "FlextInfraRefactorCensus",
    ),
    "FlextInfraRefactorClassNestingAnalyzer": (
        "flext_infra.refactor.class_nesting_analyzer",
        "FlextInfraRefactorClassNestingAnalyzer",
    ),
    "FlextInfraRefactorClassReconstructorRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorClassReconstructorRule",
    ),
    "FlextInfraRefactorEngine": (
        "flext_infra.refactor.engine",
        "FlextInfraRefactorEngine",
    ),
    "FlextInfraRefactorEngineHelpersMixin": (
        "flext_infra.refactor._engine_helpers",
        "FlextInfraRefactorEngineHelpersMixin",
    ),
    "FlextInfraRefactorLegacyRemovalTextRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorLegacyRemovalTextRule",
    ),
    "FlextInfraRefactorLooseClassScanner": (
        "flext_infra.refactor.scanner",
        "FlextInfraRefactorLooseClassScanner",
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
    "FlextInfraRefactorMROResolver": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROResolver",
    ),
    "FlextInfraRefactorMigrateToClassMRO": (
        "flext_infra.refactor.migrate_to_class_mro",
        "FlextInfraRefactorMigrateToClassMRO",
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
    "FlextInfraRefactorSymbolPropagationRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorSymbolPropagationRule",
    ),
    "FlextInfraRefactorTier0ImportFixRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorTier0ImportFixRule",
    ),
    "FlextInfraRefactorTypingAnnotationFixRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorTypingAnnotationFixRule",
    ),
    "FlextInfraRefactorTypingUnificationRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorTypingUnificationRule",
    ),
    "FlextInfraRefactorViolationAnalyzer": (
        "flext_infra.refactor.violation_analyzer",
        "FlextInfraRefactorViolationAnalyzer",
    ),
    "FlextInfraUtilitiesRefactor": (
        "flext_infra.refactor._utilities",
        "FlextInfraUtilitiesRefactor",
    ),
    "FlextInfraUtilitiesRefactorCensus": (
        "flext_infra.refactor._utilities_census",
        "FlextInfraUtilitiesRefactorCensus",
    ),
    "FlextInfraUtilitiesRefactorCli": (
        "flext_infra.refactor._utilities_cli",
        "FlextInfraUtilitiesRefactorCli",
    ),
    "FlextInfraUtilitiesRefactorEngine": (
        "flext_infra.refactor._utilities_engine",
        "FlextInfraUtilitiesRefactorEngine",
    ),
    "FlextInfraUtilitiesRefactorMroScan": (
        "flext_infra.refactor._utilities_mro_scan",
        "FlextInfraUtilitiesRefactorMroScan",
    ),
    "FlextInfraUtilitiesRefactorMroTransform": (
        "flext_infra.refactor._utilities_mro_transform",
        "FlextInfraUtilitiesRefactorMroTransform",
    ),
    "FlextInfraUtilitiesRefactorNamespace": (
        "flext_infra.refactor._utilities_namespace",
        "FlextInfraUtilitiesRefactorNamespace",
    ),
    "FlextInfraUtilitiesRefactorNamespaceCommon": (
        "flext_infra.refactor._utilities_namespace_analysis",
        "FlextInfraUtilitiesRefactorNamespaceCommon",
    ),
    "FlextInfraUtilitiesRefactorNamespaceFacades": (
        "flext_infra.refactor._utilities_namespace_facades",
        "FlextInfraUtilitiesRefactorNamespaceFacades",
    ),
    "FlextInfraUtilitiesRefactorNamespaceMoves": (
        "flext_infra.refactor._utilities_namespace_moves",
        "FlextInfraUtilitiesRefactorNamespaceMoves",
    ),
    "FlextInfraUtilitiesRefactorNamespaceMro": (
        "flext_infra.refactor._utilities_namespace_analysis",
        "FlextInfraUtilitiesRefactorNamespaceMro",
    ),
    "FlextInfraUtilitiesRefactorNamespaceRuntime": (
        "flext_infra.refactor._utilities_namespace_runtime",
        "FlextInfraUtilitiesRefactorNamespaceRuntime",
    ),
    "FlextInfraUtilitiesRefactorPolicy": (
        "flext_infra.refactor._utilities_policy",
        "FlextInfraUtilitiesRefactorPolicy",
    ),
    "FlextInfraUtilitiesRefactorPydantic": (
        "flext_infra.refactor._utilities_pydantic",
        "FlextInfraUtilitiesRefactorPydantic",
    ),
    "FlextInfraUtilitiesRefactorPydanticAnalysis": (
        "flext_infra.refactor._utilities_pydantic_analysis",
        "FlextInfraUtilitiesRefactorPydanticAnalysis",
    ),
    "_base_rule": "flext_infra.refactor._base_rule",
    "_engine_helpers": "flext_infra.refactor._engine_helpers",
    "_engine_rules": "flext_infra.refactor._engine_rules",
    "_namespace_enforcer_phases": "flext_infra.refactor._namespace_enforcer_phases",
    "_utilities": "flext_infra.refactor._utilities",
    "_utilities_census": "flext_infra.refactor._utilities_census",
    "_utilities_cli": "flext_infra.refactor._utilities_cli",
    "_utilities_engine": "flext_infra.refactor._utilities_engine",
    "_utilities_mro_scan": "flext_infra.refactor._utilities_mro_scan",
    "_utilities_mro_transform": "flext_infra.refactor._utilities_mro_transform",
    "_utilities_namespace": "flext_infra.refactor._utilities_namespace",
    "_utilities_namespace_analysis": "flext_infra.refactor._utilities_namespace_analysis",
    "_utilities_namespace_facades": "flext_infra.refactor._utilities_namespace_facades",
    "_utilities_namespace_moves": "flext_infra.refactor._utilities_namespace_moves",
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
    "FlextInfraCliRefactor",
    "FlextInfraGenericTransformerRule",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerPhasesMixin",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorEngineHelpersMixin",
    "FlextInfraRefactorLegacyRemovalTextRule",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROClassMigrationTextRule",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
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
    "_engine_helpers",
    "_engine_rules",
    "_namespace_enforcer_phases",
    "_utilities",
    "_utilities_census",
    "_utilities_cli",
    "_utilities_engine",
    "_utilities_mro_scan",
    "_utilities_mro_transform",
    "_utilities_namespace",
    "_utilities_namespace_analysis",
    "_utilities_namespace_facades",
    "_utilities_namespace_moves",
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
