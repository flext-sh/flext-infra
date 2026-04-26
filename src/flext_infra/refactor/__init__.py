# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".accessor_migration": ("FlextInfraAccessorMigrationOrchestrator",),
        ".census": ("FlextInfraRefactorCensus",),
        ".class_nesting_analyzer": ("FlextInfraRefactorClassNestingAnalyzer",),
        ".engine": ("FlextInfraRefactorEngine",),
        ".engine_file": (
            "FlextInfraClassNestingPostCheckGate",
            "FlextInfraRefactorFileExecutor",
        ),
        ".engine_legacy": ("FlextInfraRefactorLegacyTextOps",),
        ".engine_text": ("FlextInfraRefactorTextExecutor",),
        ".loader": ("FlextInfraRefactorRuleLoader",),
        ".migrate_to_class_mro": ("FlextInfraRefactorMigrateToClassMRO",),
        ".mro_import_rewriter": ("FlextInfraRefactorMROImportRewriter",),
        ".mro_migration_validator": ("FlextInfraRefactorMROMigrationValidator",),
        ".mro_resolver": ("FlextInfraRefactorMROResolver",),
        ".namespace_enforcer": ("FlextInfraNamespaceEnforcer",),
        ".namespace_enforcer_phases": ("FlextInfraNamespaceEnforcerPhasesMixin",),
        ".orchestrator": ("FlextInfraRefactorOrchestrator",),
        ".project_classifier": ("FlextInfraProjectClassifier",),
        ".safety": ("FlextInfraRefactorSafetyManager",),
        ".scanner": ("FlextInfraRefactorLooseClassScanner",),
        ".violation_analyzer": ("FlextInfraRefactorViolationAnalyzer",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
