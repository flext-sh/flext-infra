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
    import flext_infra.refactor._engine_rules as _flext_infra_refactor__engine_rules
    from flext_infra.refactor._base_rule import (
        FlextInfraGenericTransformerRule,
        FlextInfraRefactorRule,
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
    import flext_infra.refactor.census as _flext_infra_refactor_census
    from flext_infra.refactor._namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin,
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
    "FlextInfraGenericTransformerRule": (
        "flext_infra.refactor._base_rule",
        "FlextInfraGenericTransformerRule",
    ),
    "FlextInfraCliRefactor": ("flext_infra.refactor.cli", "FlextInfraCliRefactor"),
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
    "FlextInfraRefactorSignaturePropagationRule": (
        "flext_infra.refactor._engine_rules",
        "FlextInfraRefactorSignaturePropagationRule",
    ),
    "FlextInfraRefactorSafetyManager": (
        "flext_infra.refactor.safety",
        "FlextInfraRefactorSafetyManager",
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
    "_base_rule": "flext_infra.refactor._base_rule",
    "_engine_rules": "flext_infra.refactor._engine_rules",
    "_namespace_enforcer_phases": "flext_infra.refactor._namespace_enforcer_phases",
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
    "_base_rule",
    "_engine_rules",
    "_namespace_enforcer_phases",
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
