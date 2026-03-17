# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Public API for flext_infra.refactor with lazy loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from flext_infra.refactor.analysis import (
        FlextInfraRefactorClassNestingAnalyzer,
        FlextInfraRefactorViolationAnalyzer,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.dependency_analyzer import (
        ClassPlacementDetector,
        CompatibilityAliasDetector,
        CyclicImportDetector,
        DependencyAnalyzer,
        FlextInfraRefactorDependencyAnalyzerFacade,
        FutureAnnotationsDetector,
        ImportAliasDetector,
        InternalImportDetector,
        LooseObjectDetector,
        ManualProtocolDetector,
        ManualTypingAliasDetector,
        MROCompletenessDetector,
        NamespaceFacadeScanner,
        NamespaceSourceDetector,
        RuntimeAliasDetector,
    )
    from flext_infra.refactor.engine import FlextInfraRefactorEngine
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.mro_migrator import (
        FlextInfraRefactorMROMigrationTransformer,
    )
    from flext_infra.refactor.mro_resolver import (
        FlextInfraRefactorMROImportRewriter,
        FlextInfraRefactorMROMigrationScanner,
        FlextInfraRefactorMROResolver,
    )
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
    from flext_infra.refactor.namespace_rewriter import NamespaceEnforcementRewriter
    from flext_infra.refactor.output import FlextInfraRefactorOutputRenderer
    from flext_infra.refactor.project_classifier import ProjectClassifier
    from flext_infra.refactor.pydantic_centralizer import (
        FlextInfraRefactorPydanticCentralizer,
    )
    from flext_infra.refactor.rule import (
        FlextInfraRefactorRule,
        FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.validation import (
        FlextInfraRefactorCliSupport,
        FlextInfraRefactorMROMigrationValidator,
        FlextInfraRefactorRuleDefinitionValidator,
        PostCheckGate,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ClassPlacementDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ClassPlacementDetector",
    ),
    "CompatibilityAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "CompatibilityAliasDetector",
    ),
    "CyclicImportDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "CyclicImportDetector",
    ),
    "DependencyAnalyzer": (
        "flext_infra.refactor.dependency_analyzer",
        "DependencyAnalyzer",
    ),
    "FlextInfraNamespaceEnforcer": (
        "flext_infra.refactor.namespace_enforcer",
        "FlextInfraNamespaceEnforcer",
    ),
    "FlextInfraRefactorCensus": (
        "flext_infra.refactor.census",
        "FlextInfraRefactorCensus",
    ),
    "FlextInfraRefactorClassNestingAnalyzer": (
        "flext_infra.refactor.analysis",
        "FlextInfraRefactorClassNestingAnalyzer",
    ),
    "FlextInfraRefactorCliSupport": (
        "flext_infra.refactor.validation",
        "FlextInfraRefactorCliSupport",
    ),
    "FlextInfraRefactorDependencyAnalyzerFacade": (
        "flext_infra.refactor.dependency_analyzer",
        "FlextInfraRefactorDependencyAnalyzerFacade",
    ),
    "FlextInfraRefactorEngine": (
        "flext_infra.refactor.engine",
        "FlextInfraRefactorEngine",
    ),
    "FlextInfraRefactorLooseClassScanner": (
        "flext_infra.refactor.scanner",
        "FlextInfraRefactorLooseClassScanner",
    ),
    "FlextInfraRefactorMROImportRewriter": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROImportRewriter",
    ),
    "FlextInfraRefactorMROMigrationScanner": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROMigrationScanner",
    ),
    "FlextInfraRefactorMROMigrationTransformer": (
        "flext_infra.refactor.mro_migrator",
        "FlextInfraRefactorMROMigrationTransformer",
    ),
    "FlextInfraRefactorMROMigrationValidator": (
        "flext_infra.refactor.validation",
        "FlextInfraRefactorMROMigrationValidator",
    ),
    "FlextInfraRefactorMROResolver": (
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROResolver",
    ),
    "FlextInfraRefactorMigrateToClassMRO": (
        "flext_infra.refactor.migrate_to_class_mro",
        "FlextInfraRefactorMigrateToClassMRO",
    ),
    "FlextInfraRefactorOutputRenderer": (
        "flext_infra.refactor.output",
        "FlextInfraRefactorOutputRenderer",
    ),
    "FlextInfraRefactorPydanticCentralizer": (
        "flext_infra.refactor.pydantic_centralizer",
        "FlextInfraRefactorPydanticCentralizer",
    ),
    "FlextInfraRefactorRule": ("flext_infra.refactor.rule", "FlextInfraRefactorRule"),
    "FlextInfraRefactorRuleDefinitionValidator": (
        "flext_infra.refactor.validation",
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
    "FlextInfraRefactorViolationAnalyzer": (
        "flext_infra.refactor.analysis",
        "FlextInfraRefactorViolationAnalyzer",
    ),
    "FutureAnnotationsDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "FutureAnnotationsDetector",
    ),
    "ImportAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ImportAliasDetector",
    ),
    "InternalImportDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "InternalImportDetector",
    ),
    "LooseObjectDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "LooseObjectDetector",
    ),
    "MROCompletenessDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "MROCompletenessDetector",
    ),
    "ManualProtocolDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ManualProtocolDetector",
    ),
    "ManualTypingAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "ManualTypingAliasDetector",
    ),
    "NamespaceEnforcementRewriter": (
        "flext_infra.refactor.namespace_rewriter",
        "NamespaceEnforcementRewriter",
    ),
    "NamespaceFacadeScanner": (
        "flext_infra.refactor.dependency_analyzer",
        "NamespaceFacadeScanner",
    ),
    "NamespaceSourceDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "NamespaceSourceDetector",
    ),
    "PostCheckGate": ("flext_infra.refactor.validation", "PostCheckGate"),
    "ProjectClassifier": (
        "flext_infra.refactor.project_classifier",
        "ProjectClassifier",
    ),
    "RuntimeAliasDetector": (
        "flext_infra.refactor.dependency_analyzer",
        "RuntimeAliasDetector",
    ),
}

__all__ = [
    "ClassPlacementDetector",
    "CompatibilityAliasDetector",
    "CyclicImportDetector",
    "DependencyAnalyzer",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorCliSupport",
    "FlextInfraRefactorDependencyAnalyzerFacade",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationScanner",
    "FlextInfraRefactorMROMigrationTransformer",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorOutputRenderer",
    "FlextInfraRefactorPydanticCentralizer",
    "FlextInfraRefactorRule",
    "FlextInfraRefactorRuleDefinitionValidator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorViolationAnalyzer",
    "FutureAnnotationsDetector",
    "ImportAliasDetector",
    "InternalImportDetector",
    "LooseObjectDetector",
    "MROCompletenessDetector",
    "ManualProtocolDetector",
    "ManualTypingAliasDetector",
    "NamespaceEnforcementRewriter",
    "NamespaceFacadeScanner",
    "NamespaceSourceDetector",
    "PostCheckGate",
    "ProjectClassifier",
    "RuntimeAliasDetector",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
