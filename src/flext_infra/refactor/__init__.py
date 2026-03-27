# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Public API for flext_infra.refactor with lazy loading."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

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
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraNamespaceEnforcer": [
        "flext_infra.refactor.namespace_enforcer",
        "FlextInfraNamespaceEnforcer",
    ],
    "FlextInfraProjectClassifier": [
        "flext_infra.refactor.project_classifier",
        "FlextInfraProjectClassifier",
    ],
    "FlextInfraRefactorCensus": [
        "flext_infra.refactor.census",
        "FlextInfraRefactorCensus",
    ],
    "FlextInfraRefactorClassNestingAnalyzer": [
        "flext_infra.refactor.class_nesting_analyzer",
        "FlextInfraRefactorClassNestingAnalyzer",
    ],
    "FlextInfraRefactorEngine": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorEngine",
    ],
    "FlextInfraRefactorLooseClassScanner": [
        "flext_infra.refactor.scanner",
        "FlextInfraRefactorLooseClassScanner",
    ],
    "FlextInfraRefactorMROImportRewriter": [
        "flext_infra.refactor.mro_import_rewriter",
        "FlextInfraRefactorMROImportRewriter",
    ],
    "FlextInfraRefactorMROMigrationValidator": [
        "flext_infra.refactor.mro_migration_validator",
        "FlextInfraRefactorMROMigrationValidator",
    ],
    "FlextInfraRefactorMROResolver": [
        "flext_infra.refactor.mro_resolver",
        "FlextInfraRefactorMROResolver",
    ],
    "FlextInfraRefactorMigrateToClassMRO": [
        "flext_infra.refactor.migrate_to_class_mro",
        "FlextInfraRefactorMigrateToClassMRO",
    ],
    "FlextInfraRefactorRule": ["flext_infra.refactor.rule", "FlextInfraRefactorRule"],
    "FlextInfraRefactorRuleDefinitionValidator": [
        "flext_infra.refactor.rule_definition_validator",
        "FlextInfraRefactorRuleDefinitionValidator",
    ],
    "FlextInfraRefactorRuleLoader": [
        "flext_infra.refactor.rule",
        "FlextInfraRefactorRuleLoader",
    ],
    "FlextInfraRefactorSafetyManager": [
        "flext_infra.refactor.safety",
        "FlextInfraRefactorSafetyManager",
    ],
    "FlextInfraRefactorViolationAnalyzer": [
        "flext_infra.refactor.violation_analyzer",
        "FlextInfraRefactorViolationAnalyzer",
    ],
}

__all__ = [
    "FlextInfraNamespaceEnforcer",
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
