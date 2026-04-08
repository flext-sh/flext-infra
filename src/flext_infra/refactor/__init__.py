# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

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
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
