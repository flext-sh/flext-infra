# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.classvar_constant_autofix import (
        FlextInfraRefactorClassvarConstantAutofix,
    )
    from flext_infra.refactor.declarative_enforcement import (
        FlextInfraRefactorDeclarativeEnforcement,
    )
    from flext_infra.refactor.file_executor import (
        FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor,
    )
    from flext_infra.refactor.legacy_text_ops import FlextInfraRefactorLegacyTextOps
    from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.modernize_orchestrator import (
        FlextInfraModernizeOrchestrator,
    )
    from flext_infra.refactor.mro_import_rewriter import (
        FlextInfraRefactorMROImportRewriter,
    )
    from flext_infra.refactor.mro_migration_validator import (
        FlextInfraRefactorMROMigrationValidator,
    )
    from flext_infra.refactor.mro_resolver import FlextInfraRefactorMROResolver
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
    from flext_infra.refactor.namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin,
    )
    from flext_infra.refactor.orchestrator import FlextInfraRefactorOrchestrator
    from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.service import FlextInfraRefactorService
    from flext_infra.refactor.text_executor import FlextInfraRefactorTextExecutor
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.refactor.wrapper_root_namespace import (
        FlextInfraWrapperRootNamespaceRefactor,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
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
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
