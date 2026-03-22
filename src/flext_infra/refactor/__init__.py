# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Public API for flext_infra.refactor with lazy loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.refactor import _detectors
    from flext_infra.refactor._detectors.class_placement_detector import (
        ClassPlacementDetector,
    )
    from flext_infra.refactor._detectors.compatibility_alias_detector import (
        CompatibilityAliasDetector,
    )
    from flext_infra.refactor._detectors.cyclic_import_detector import (
        CyclicImportDetector,
    )
    from flext_infra.refactor._detectors.dependency_analyzer_base import (
        DependencyAnalyzer,
    )
    from flext_infra.refactor._detectors.future_annotations_detector import (
        FutureAnnotationsDetector,
    )
    from flext_infra.refactor._detectors.import_alias_detector import (
        ImportAliasDetector,
    )
    from flext_infra.refactor._detectors.import_collector import ImportCollector
    from flext_infra.refactor._detectors.internal_import_detector import (
        InternalImportDetector,
    )
    from flext_infra.refactor._detectors.loose_object_detector import (
        LooseObjectDetector,
    )
    from flext_infra.refactor._detectors.manual_protocol_detector import (
        ManualProtocolDetector,
    )
    from flext_infra.refactor._detectors.manual_typing_alias_detector import (
        ManualTypingAliasDetector,
    )
    from flext_infra.refactor._detectors.mro_completeness_detector import (
        MROCompletenessDetector,
    )
    from flext_infra.refactor._detectors.namespace_facade_scanner import (
        NamespaceFacadeScanner,
    )
    from flext_infra.refactor._detectors.namespace_source_detector import (
        NamespaceSourceDetector,
    )
    from flext_infra.refactor._detectors.python_module_loader_mixin import (
        FlextInfraRefactorDetectorPythonModuleLoaderMixin,
    )
    from flext_infra.refactor._detectors.runtime_alias_detector import (
        RuntimeAliasDetector,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.engine import FlextInfraRefactorEngine
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO,
    )
    from flext_infra.refactor.mro_import_rewriter import (
        FlextInfraRefactorMROImportRewriter,
    )
    from flext_infra.refactor.mro_migration_validator import (
        FlextInfraRefactorMROMigrationValidator,
    )
    from flext_infra.refactor.mro_resolver import FlextInfraRefactorMROResolver
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
    from flext_infra.refactor.project_classifier import ProjectClassifier
    from flext_infra.refactor.rule import (
        FlextInfraRefactorRule,
        FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.rule_definition_validator import (
        FlextInfraRefactorRuleDefinitionValidator,
    )
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.validation import PostCheckGate
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ClassPlacementDetector": ("flext_infra.refactor._detectors.class_placement_detector", "ClassPlacementDetector"),
    "CompatibilityAliasDetector": ("flext_infra.refactor._detectors.compatibility_alias_detector", "CompatibilityAliasDetector"),
    "CyclicImportDetector": ("flext_infra.refactor._detectors.cyclic_import_detector", "CyclicImportDetector"),
    "DependencyAnalyzer": ("flext_infra.refactor._detectors.dependency_analyzer_base", "DependencyAnalyzer"),
    "FlextInfraNamespaceEnforcer": ("flext_infra.refactor.namespace_enforcer", "FlextInfraNamespaceEnforcer"),
    "FlextInfraRefactorCensus": ("flext_infra.refactor.census", "FlextInfraRefactorCensus"),
    "FlextInfraRefactorClassNestingAnalyzer": ("flext_infra.refactor.class_nesting_analyzer", "FlextInfraRefactorClassNestingAnalyzer"),
    "FlextInfraRefactorDetectorPythonModuleLoaderMixin": ("flext_infra.refactor._detectors.python_module_loader_mixin", "FlextInfraRefactorDetectorPythonModuleLoaderMixin"),
    "FlextInfraRefactorEngine": ("flext_infra.refactor.engine", "FlextInfraRefactorEngine"),
    "FlextInfraRefactorLooseClassScanner": ("flext_infra.refactor.scanner", "FlextInfraRefactorLooseClassScanner"),
    "FlextInfraRefactorMROImportRewriter": ("flext_infra.refactor.mro_import_rewriter", "FlextInfraRefactorMROImportRewriter"),
    "FlextInfraRefactorMROMigrationValidator": ("flext_infra.refactor.mro_migration_validator", "FlextInfraRefactorMROMigrationValidator"),
    "FlextInfraRefactorMROResolver": ("flext_infra.refactor.mro_resolver", "FlextInfraRefactorMROResolver"),
    "FlextInfraRefactorMigrateToClassMRO": ("flext_infra.refactor.migrate_to_class_mro", "FlextInfraRefactorMigrateToClassMRO"),
    "FlextInfraRefactorRule": ("flext_infra.refactor.rule", "FlextInfraRefactorRule"),
    "FlextInfraRefactorRuleDefinitionValidator": ("flext_infra.refactor.rule_definition_validator", "FlextInfraRefactorRuleDefinitionValidator"),
    "FlextInfraRefactorRuleLoader": ("flext_infra.refactor.rule", "FlextInfraRefactorRuleLoader"),
    "FlextInfraRefactorSafetyManager": ("flext_infra.refactor.safety", "FlextInfraRefactorSafetyManager"),
    "FlextInfraRefactorViolationAnalyzer": ("flext_infra.refactor.violation_analyzer", "FlextInfraRefactorViolationAnalyzer"),
    "FutureAnnotationsDetector": ("flext_infra.refactor._detectors.future_annotations_detector", "FutureAnnotationsDetector"),
    "ImportAliasDetector": ("flext_infra.refactor._detectors.import_alias_detector", "ImportAliasDetector"),
    "ImportCollector": ("flext_infra.refactor._detectors.import_collector", "ImportCollector"),
    "InternalImportDetector": ("flext_infra.refactor._detectors.internal_import_detector", "InternalImportDetector"),
    "LooseObjectDetector": ("flext_infra.refactor._detectors.loose_object_detector", "LooseObjectDetector"),
    "MROCompletenessDetector": ("flext_infra.refactor._detectors.mro_completeness_detector", "MROCompletenessDetector"),
    "ManualProtocolDetector": ("flext_infra.refactor._detectors.manual_protocol_detector", "ManualProtocolDetector"),
    "ManualTypingAliasDetector": ("flext_infra.refactor._detectors.manual_typing_alias_detector", "ManualTypingAliasDetector"),
    "NamespaceFacadeScanner": ("flext_infra.refactor._detectors.namespace_facade_scanner", "NamespaceFacadeScanner"),
    "NamespaceSourceDetector": ("flext_infra.refactor._detectors.namespace_source_detector", "NamespaceSourceDetector"),
    "PostCheckGate": ("flext_infra.refactor.validation", "PostCheckGate"),
    "ProjectClassifier": ("flext_infra.refactor.project_classifier", "ProjectClassifier"),
    "RuntimeAliasDetector": ("flext_infra.refactor._detectors.runtime_alias_detector", "RuntimeAliasDetector"),
    "_detectors": ("flext_infra.refactor._detectors", ""),
}

__all__ = [
    "ClassPlacementDetector",
    "CompatibilityAliasDetector",
    "CyclicImportDetector",
    "DependencyAnalyzer",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorDetectorPythonModuleLoaderMixin",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorRule",
    "FlextInfraRefactorRuleDefinitionValidator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorViolationAnalyzer",
    "FutureAnnotationsDetector",
    "ImportAliasDetector",
    "ImportCollector",
    "InternalImportDetector",
    "LooseObjectDetector",
    "MROCompletenessDetector",
    "ManualProtocolDetector",
    "ManualTypingAliasDetector",
    "NamespaceFacadeScanner",
    "NamespaceSourceDetector",
    "PostCheckGate",
    "ProjectClassifier",
    "RuntimeAliasDetector",
    "_detectors",
]


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
