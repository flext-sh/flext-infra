# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .accessor_migration import FlextInfraAccessorMigrationOrchestrator
    from .census import FlextInfraRefactorCensus
    from .class_nesting_analyzer import FlextInfraRefactorClassNestingAnalyzer
    from .classvar_constant_autofix import FlextInfraRefactorClassvarConstantAutofix
    from .declarative_enforcement import FlextInfraRefactorDeclarativeEnforcement
    from .file_executor import (
        FlextInfraClassNestingPostCheckGate,
        FlextInfraRefactorFileExecutor,
    )
    from .legacy_text_ops import FlextInfraRefactorLegacyTextOps
    from .loader import FlextInfraRefactorRuleLoader
    from .migrate_to_class_mro import FlextInfraRefactorMigrateToClassMRO
    from .modernize_orchestrator import FlextInfraModernizeOrchestrator
    from .mro_import_rewriter import FlextInfraRefactorMROImportRewriter
    from .mro_migration_validator import FlextInfraRefactorMROMigrationValidator
    from .mro_resolver import FlextInfraRefactorMROResolver
    from .namespace_enforcer import FlextInfraNamespaceEnforcer
    from .namespace_enforcer_phases import FlextInfraNamespaceEnforcerPhasesMixin
    from .orchestrator import FlextInfraRefactorOrchestrator
    from .project_classifier import FlextInfraProjectClassifier
    from .safety import FlextInfraRefactorSafetyManager
    from .scanner import FlextInfraRefactorLooseClassScanner
    from .service import FlextInfraRefactorService
    from .text_executor import FlextInfraRefactorTextExecutor
    from .violation_analyzer import FlextInfraRefactorViolationAnalyzer
    from .wrapper_root_namespace import FlextInfraWrapperRootNamespaceRefactor
__all__: tuple[str, ...] = (
    "FlextInfraAccessorMigrationOrchestrator",
    "FlextInfraClassNestingPostCheckGate",
    "FlextInfraModernizeOrchestrator",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceEnforcerPhasesMixin",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassvarConstantAutofix",
    "FlextInfraRefactorDeclarativeEnforcement",
    "FlextInfraRefactorFileExecutor",
    "FlextInfraRefactorLegacyTextOps",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorOrchestrator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorService",
    "FlextInfraRefactorTextExecutor",
    "FlextInfraRefactorViolationAnalyzer",
    "FlextInfraWrapperRootNamespaceRefactor",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".accessor_migration": ("FlextInfraAccessorMigrationOrchestrator",),
            ".census": ("FlextInfraRefactorCensus",),
            ".class_nesting_analyzer": ("FlextInfraRefactorClassNestingAnalyzer",),
            ".classvar_constant_autofix": (
                "FlextInfraRefactorClassvarConstantAutofix",
            ),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
