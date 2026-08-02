# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.refactor package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".accessor_migration": ("FlextInfraAccessorMigrationOrchestrator",),
    ".census": ("FlextInfraRefactorCensus",),
    ".class_nesting_analyzer": ("FlextInfraRefactorClassNestingAnalyzer",),
    ".classvar_constant_autofix": ("FlextInfraRefactorClassvarConstantAutofix",),
    ".declarative_enforcement": ("FlextInfraRefactorDeclarativeEnforcement",),
    ".file_executor": (
        "FlextInfraClassNestingPostCheckGate",
        "FlextInfraRefactorFileExecutor",
    ),
    ".legacy_text_ops": ("FlextInfraRefactorLegacyTextOps",),
    ".loader": ("FlextInfraRefactorRuleLoader",),
    ".migrate_to_class_mro": ("FlextInfraRefactorMigrateToClassMRO",),
    ".modernize_orchestrator": ("FlextInfraModernizeOrchestrator",),
    ".mro_import_rewriter": ("FlextInfraRefactorMROImportRewriter",),
    ".mro_migration_validator": ("FlextInfraRefactorMROMigrationValidator",),
    ".mro_resolver": ("FlextInfraRefactorMROResolver",),
    ".namespace_enforcer": ("FlextInfraNamespaceEnforcer",),
    ".namespace_enforcer_phases": ("FlextInfraNamespaceEnforcerPhasesMixin",),
    ".orchestrator": ("FlextInfraRefactorOrchestrator",),
    ".project_classifier": ("FlextInfraProjectClassifier",),
    ".safety": ("FlextInfraRefactorSafetyManager",),
    ".scanner": ("FlextInfraRefactorLooseClassScanner",),
    ".service": ("FlextInfraRefactorService",),
    ".text_executor": ("FlextInfraRefactorTextExecutor",),
    ".violation_analyzer": ("FlextInfraRefactorViolationAnalyzer",),
    ".wrapper_root_namespace": ("FlextInfraWrapperRootNamespaceRefactor",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
