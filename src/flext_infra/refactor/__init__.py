# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Public API for flext_infra.refactor with lazy loading."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.refactor import _detectors
    from flext_infra.refactor._detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector,
    )
    from flext_infra.refactor._detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.refactor._detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector,
    )
    from flext_infra.refactor._detectors.dependency_analyzer_base import (
        FlextInfraDependencyAnalyzer,
    )
    from flext_infra.refactor._detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.refactor._detectors.import_alias_detector import (
        FlextInfraImportAliasDetector,
    )
    from flext_infra.refactor._detectors.import_collector import (
        FlextInfraImportCollector,
    )
    from flext_infra.refactor._detectors.internal_import_detector import (
        FlextInfraInternalImportDetector,
    )
    from flext_infra.refactor._detectors.loose_object_detector import (
        FlextInfraLooseObjectDetector,
    )
    from flext_infra.refactor._detectors.manual_protocol_detector import (
        FlextInfraManualProtocolDetector,
    )
    from flext_infra.refactor._detectors.manual_typing_alias_detector import (
        FlextInfraManualTypingAliasDetector,
    )
    from flext_infra.refactor._detectors.mro_completeness_detector import (
        FlextInfraMROCompletenessDetector,
    )
    from flext_infra.refactor._detectors.namespace_facade_scanner import (
        FlextInfraNamespaceFacadeScanner,
    )
    from flext_infra.refactor._detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.refactor._detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector,
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
    from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
    from flext_infra.refactor.rule import (
        FlextInfraRefactorRule,
        FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.rule_definition_validator import (
        FlextInfraRefactorRuleDefinitionValidator,
    )
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.validation import FlextInfraPostCheckGate
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )

_LAZY_IMPORTS: Mapping[str, tuple[str, str]] = {
    "FlextInfraClassPlacementDetector": ("flext_infra.refactor._detectors.class_placement_detector", "FlextInfraClassPlacementDetector"),
    "FlextInfraCompatibilityAliasDetector": ("flext_infra.refactor._detectors.compatibility_alias_detector", "FlextInfraCompatibilityAliasDetector"),
    "FlextInfraCyclicImportDetector": ("flext_infra.refactor._detectors.cyclic_import_detector", "FlextInfraCyclicImportDetector"),
    "FlextInfraDependencyAnalyzer": ("flext_infra.refactor._detectors.dependency_analyzer_base", "FlextInfraDependencyAnalyzer"),
    "FlextInfraFutureAnnotationsDetector": ("flext_infra.refactor._detectors.future_annotations_detector", "FlextInfraFutureAnnotationsDetector"),
    "FlextInfraImportAliasDetector": ("flext_infra.refactor._detectors.import_alias_detector", "FlextInfraImportAliasDetector"),
    "FlextInfraImportCollector": ("flext_infra.refactor._detectors.import_collector", "FlextInfraImportCollector"),
    "FlextInfraInternalImportDetector": ("flext_infra.refactor._detectors.internal_import_detector", "FlextInfraInternalImportDetector"),
    "FlextInfraLooseObjectDetector": ("flext_infra.refactor._detectors.loose_object_detector", "FlextInfraLooseObjectDetector"),
    "FlextInfraMROCompletenessDetector": ("flext_infra.refactor._detectors.mro_completeness_detector", "FlextInfraMROCompletenessDetector"),
    "FlextInfraManualProtocolDetector": ("flext_infra.refactor._detectors.manual_protocol_detector", "FlextInfraManualProtocolDetector"),
    "FlextInfraManualTypingAliasDetector": ("flext_infra.refactor._detectors.manual_typing_alias_detector", "FlextInfraManualTypingAliasDetector"),
    "FlextInfraNamespaceEnforcer": ("flext_infra.refactor.namespace_enforcer", "FlextInfraNamespaceEnforcer"),
    "FlextInfraNamespaceFacadeScanner": ("flext_infra.refactor._detectors.namespace_facade_scanner", "FlextInfraNamespaceFacadeScanner"),
    "FlextInfraNamespaceSourceDetector": ("flext_infra.refactor._detectors.namespace_source_detector", "FlextInfraNamespaceSourceDetector"),
    "FlextInfraPostCheckGate": ("flext_infra.refactor.validation", "FlextInfraPostCheckGate"),
    "FlextInfraProjectClassifier": ("flext_infra.refactor.project_classifier", "FlextInfraProjectClassifier"),
    "FlextInfraRefactorCensus": ("flext_infra.refactor.census", "FlextInfraRefactorCensus"),
    "FlextInfraRefactorClassNestingAnalyzer": ("flext_infra.refactor.class_nesting_analyzer", "FlextInfraRefactorClassNestingAnalyzer"),
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
    "FlextInfraRuntimeAliasDetector": ("flext_infra.refactor._detectors.runtime_alias_detector", "FlextInfraRuntimeAliasDetector"),
    "_detectors": ("flext_infra.refactor._detectors", ""),
}

__all__ = [
    "FlextInfraClassPlacementDetector",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDependencyAnalyzer",
    "FlextInfraFutureAnnotationsDetector",
    "FlextInfraImportAliasDetector",
    "FlextInfraImportCollector",
    "FlextInfraInternalImportDetector",
    "FlextInfraLooseObjectDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceFacadeScanner",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraPostCheckGate",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
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
    "FlextInfraRuntimeAliasDetector",
    "_detectors",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
