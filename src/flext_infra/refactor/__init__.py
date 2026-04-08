# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._base_rule": (
            "FlextInfraGenericTransformerRule",
            "FlextInfraRefactorRule",
        ),
        "._engine_helpers": ("FlextInfraRefactorEngineHelpersMixin",),
        "._engine_rules": (
            "FlextInfraRefactorClassReconstructorRule",
            "FlextInfraRefactorLegacyRemovalTextRule",
            "FlextInfraRefactorMROClassMigrationTextRule",
            "FlextInfraRefactorMRORedundancyChecker",
            "FlextInfraRefactorPatternCorrectionsTextRule",
            "FlextInfraRefactorSignaturePropagationRule",
            "FlextInfraRefactorSymbolPropagationRule",
            "FlextInfraRefactorTier0ImportFixRule",
            "FlextInfraRefactorTypingAnnotationFixRule",
            "FlextInfraRefactorTypingUnificationRule",
        ),
        "._namespace_enforcer_phases": ("FlextInfraNamespaceEnforcerPhasesMixin",),
        ".census": ("FlextInfraRefactorCensus",),
        ".class_nesting_analyzer": ("FlextInfraRefactorClassNestingAnalyzer",),
        ".cli": ("FlextInfraCliRefactor",),
        ".engine": ("FlextInfraRefactorEngine",),
        ".migrate_to_class_mro": ("FlextInfraRefactorMigrateToClassMRO",),
        ".mro_import_rewriter": ("FlextInfraRefactorMROImportRewriter",),
        ".mro_migration_validator": ("FlextInfraRefactorMROMigrationValidator",),
        ".mro_resolver": ("FlextInfraRefactorMROResolver",),
        ".namespace_enforcer": ("FlextInfraNamespaceEnforcer",),
        ".project_classifier": ("FlextInfraProjectClassifier",),
        ".rule": ("FlextInfraRefactorRuleLoader",),
        ".rule_definition_validator": ("FlextInfraRefactorRuleDefinitionValidator",),
        ".safety": ("FlextInfraRefactorSafetyManager",),
        ".scanner": ("FlextInfraRefactorLooseClassScanner",),
        ".violation_analyzer": ("FlextInfraRefactorViolationAnalyzer",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
