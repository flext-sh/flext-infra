# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCliRefactor": ".cli",
    "FlextInfraGenericTransformerRule": "._base_rule",
    "FlextInfraNamespaceEnforcer": ".namespace_enforcer",
    "FlextInfraNamespaceEnforcerPhasesMixin": "._namespace_enforcer_phases",
    "FlextInfraProjectClassifier": ".project_classifier",
    "FlextInfraRefactorCensus": ".census",
    "FlextInfraRefactorClassNestingAnalyzer": ".class_nesting_analyzer",
    "FlextInfraRefactorClassReconstructorRule": "._engine_rules",
    "FlextInfraRefactorEngine": ".engine",
    "FlextInfraRefactorEngineHelpersMixin": "._engine_helpers",
    "FlextInfraRefactorLegacyRemovalTextRule": "._engine_rules",
    "FlextInfraRefactorLooseClassScanner": ".scanner",
    "FlextInfraRefactorMROClassMigrationTextRule": "._engine_rules",
    "FlextInfraRefactorMROImportRewriter": ".mro_import_rewriter",
    "FlextInfraRefactorMROMigrationValidator": ".mro_migration_validator",
    "FlextInfraRefactorMRORedundancyChecker": "._engine_rules",
    "FlextInfraRefactorMROResolver": ".mro_resolver",
    "FlextInfraRefactorMigrateToClassMRO": ".migrate_to_class_mro",
    "FlextInfraRefactorPatternCorrectionsTextRule": "._engine_rules",
    "FlextInfraRefactorRule": "._base_rule",
    "FlextInfraRefactorRuleDefinitionValidator": ".rule_definition_validator",
    "FlextInfraRefactorRuleLoader": ".rule",
    "FlextInfraRefactorSafetyManager": ".safety",
    "FlextInfraRefactorSignaturePropagationRule": "._engine_rules",
    "FlextInfraRefactorSymbolPropagationRule": "._engine_rules",
    "FlextInfraRefactorTier0ImportFixRule": "._engine_rules",
    "FlextInfraRefactorTypingAnnotationFixRule": "._engine_rules",
    "FlextInfraRefactorTypingUnificationRule": "._engine_rules",
    "FlextInfraRefactorViolationAnalyzer": ".violation_analyzer",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
