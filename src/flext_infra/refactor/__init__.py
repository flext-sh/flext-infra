# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator as FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import (
        FlextInfraRefactorCensus as FlextInfraRefactorCensus,
    )
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer as FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.classvar_constant_autofix import (
        FlextInfraRefactorClassvarConstantAutofix as FlextInfraRefactorClassvarConstantAutofix,
    )
    from flext_infra.refactor.file_executor import (
        FlextInfraClassNestingPostCheckGate as FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor as FlextInfraRefactorFileExecutor,
    )
    from flext_infra.refactor.legacy_text_ops import (
        FlextInfraRefactorLegacyTextOps as FlextInfraRefactorLegacyTextOps,
    )
    from flext_infra.refactor.loader import (
        FlextInfraRefactorRuleLoader as FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO as FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.modernize_orchestrator import (
        FlextInfraModernizeOrchestrator as FlextInfraModernizeOrchestrator,
    )
    from flext_infra.refactor.mro_import_rewriter import (
        FlextInfraRefactorMROImportRewriter as FlextInfraRefactorMROImportRewriter,
    )
    from flext_infra.refactor.mro_migration_validator import (
        FlextInfraRefactorMROMigrationValidator as FlextInfraRefactorMROMigrationValidator,
    )
    from flext_infra.refactor.mro_resolver import (
        FlextInfraRefactorMROResolver as FlextInfraRefactorMROResolver,
    )
    from flext_infra.refactor.namespace_enforcer import (
        FlextInfraNamespaceEnforcer as FlextInfraNamespaceEnforcer,
    )
    from flext_infra.refactor.namespace_enforcer_phases import (
        FlextInfraNamespaceEnforcerPhasesMixin as FlextInfraNamespaceEnforcerPhasesMixin,
    )
    from flext_infra.refactor.orchestrator import (
        FlextInfraRefactorOrchestrator as FlextInfraRefactorOrchestrator,
    )
    from flext_infra.refactor.project_classifier import (
        FlextInfraProjectClassifier as FlextInfraProjectClassifier,
    )
    from flext_infra.refactor.safety import (
        FlextInfraRefactorSafetyManager as FlextInfraRefactorSafetyManager,
    )
    from flext_infra.refactor.scanner import (
        FlextInfraRefactorLooseClassScanner as FlextInfraRefactorLooseClassScanner,
    )
    from flext_infra.refactor.service import (
        FlextInfraRefactorService as FlextInfraRefactorService,
    )
    from flext_infra.refactor.text_executor import (
        FlextInfraRefactorTextExecutor as FlextInfraRefactorTextExecutor,
    )
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer as FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.refactor.wrapper_root_namespace import (
        FlextInfraWrapperRootNamespaceRefactor as FlextInfraWrapperRootNamespaceRefactor,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".accessor_migration": ("FlextInfraAccessorMigrationOrchestrator",),
        ".census": ("FlextInfraRefactorCensus",),
        ".class_nesting_analyzer": ("FlextInfraRefactorClassNestingAnalyzer",),
        ".classvar_constant_autofix": ("FlextInfraRefactorClassvarConstantAutofix",),
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
