# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator as FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import (
        FlextInfraRefactorCensus as FlextInfraRefactorCensus,
    )
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer as FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.engine import (
        FlextInfraRefactorEngine as FlextInfraRefactorEngine,
    )
    from flext_infra.refactor.engine_file import (
        FlextInfraClassNestingPostCheckGate as FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor as FlextInfraRefactorFileExecutor,
    )
    from flext_infra.refactor.engine_legacy import (
        FlextInfraRefactorLegacyTextOps as FlextInfraRefactorLegacyTextOps,
    )
    from flext_infra.refactor.engine_text import (
        FlextInfraRefactorTextExecutor as FlextInfraRefactorTextExecutor,
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
        ".engine": ("FlextInfraRefactorEngine",),
        ".engine_file": (
            "FlextInfraClassNestingPostCheckGate",
            "FlextInfraRefactorFileExecutor",
        ),
        ".engine_legacy": ("FlextInfraRefactorLegacyTextOps",),
        ".engine_text": ("FlextInfraRefactorTextExecutor",),
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
        ".violation_analyzer": ("FlextInfraRefactorViolationAnalyzer",),
        ".wrapper_root_namespace": ("FlextInfraWrapperRootNamespaceRefactor",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
