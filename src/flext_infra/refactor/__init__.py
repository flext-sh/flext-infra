# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Public API for flext_infra.refactor with lazy loading."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor import (
        census as census,
        class_nesting_analyzer as class_nesting_analyzer,
        cli as cli,
        engine as engine,
        migrate_to_class_mro as migrate_to_class_mro,
        mro_import_rewriter as mro_import_rewriter,
        mro_migration_validator as mro_migration_validator,
        mro_resolver as mro_resolver,
        namespace_enforcer as namespace_enforcer,
        project_classifier as project_classifier,
        rule as rule,
        rule_definition_validator as rule_definition_validator,
        safety as safety,
        scanner as scanner,
        violation_analyzer as violation_analyzer,
    )
    from flext_infra.refactor.census import (
        FlextInfraRefactorCensus as FlextInfraRefactorCensus,
    )
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer as FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.cli import FlextInfraCliRefactor as FlextInfraCliRefactor
    from flext_infra.refactor.engine import (
        FlextInfraRefactorClassReconstructorRule as FlextInfraRefactorClassReconstructorRule,
        FlextInfraRefactorEngine as FlextInfraRefactorEngine,
        FlextInfraRefactorMRORedundancyChecker as FlextInfraRefactorMRORedundancyChecker,
        FlextInfraRefactorSignaturePropagationRule as FlextInfraRefactorSignaturePropagationRule,
        FlextInfraRefactorSymbolPropagationRule as FlextInfraRefactorSymbolPropagationRule,
        FlextInfraRefactorTier0ImportFixRule as FlextInfraRefactorTier0ImportFixRule,
        FlextInfraRefactorTypingAnnotationFixRule as FlextInfraRefactorTypingAnnotationFixRule,
        FlextInfraRefactorTypingUnificationRule as FlextInfraRefactorTypingUnificationRule,
    )
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO as FlextInfraRefactorMigrateToClassMRO,
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
    from flext_infra.refactor.project_classifier import (
        FlextInfraProjectClassifier as FlextInfraProjectClassifier,
    )
    from flext_infra.refactor.rule import (
        FlextInfraRefactorRule as FlextInfraRefactorRule,
        FlextInfraRefactorRuleLoader as FlextInfraRefactorRuleLoader,
    )
    from flext_infra.refactor.rule_definition_validator import (
        FlextInfraRefactorRuleDefinitionValidator as FlextInfraRefactorRuleDefinitionValidator,
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

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliRefactor": ["flext_infra.refactor.cli", "FlextInfraCliRefactor"],
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
    "FlextInfraRefactorClassReconstructorRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorClassReconstructorRule",
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
    "FlextInfraRefactorMRORedundancyChecker": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorMRORedundancyChecker",
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
    "FlextInfraRefactorSignaturePropagationRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorSignaturePropagationRule",
    ],
    "FlextInfraRefactorSymbolPropagationRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorSymbolPropagationRule",
    ],
    "FlextInfraRefactorTier0ImportFixRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorTier0ImportFixRule",
    ],
    "FlextInfraRefactorTypingAnnotationFixRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorTypingAnnotationFixRule",
    ],
    "FlextInfraRefactorTypingUnificationRule": [
        "flext_infra.refactor.engine",
        "FlextInfraRefactorTypingUnificationRule",
    ],
    "FlextInfraRefactorViolationAnalyzer": [
        "flext_infra.refactor.violation_analyzer",
        "FlextInfraRefactorViolationAnalyzer",
    ],
    "census": ["flext_infra.refactor.census", ""],
    "class_nesting_analyzer": ["flext_infra.refactor.class_nesting_analyzer", ""],
    "cli": ["flext_infra.refactor.cli", ""],
    "engine": ["flext_infra.refactor.engine", ""],
    "migrate_to_class_mro": ["flext_infra.refactor.migrate_to_class_mro", ""],
    "mro_import_rewriter": ["flext_infra.refactor.mro_import_rewriter", ""],
    "mro_migration_validator": ["flext_infra.refactor.mro_migration_validator", ""],
    "mro_resolver": ["flext_infra.refactor.mro_resolver", ""],
    "namespace_enforcer": ["flext_infra.refactor.namespace_enforcer", ""],
    "project_classifier": ["flext_infra.refactor.project_classifier", ""],
    "rule": ["flext_infra.refactor.rule", ""],
    "rule_definition_validator": ["flext_infra.refactor.rule_definition_validator", ""],
    "safety": ["flext_infra.refactor.safety", ""],
    "scanner": ["flext_infra.refactor.scanner", ""],
    "violation_analyzer": ["flext_infra.refactor.violation_analyzer", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliRefactor",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorClassNestingAnalyzer",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorLooseClassScanner",
    "FlextInfraRefactorMROImportRewriter",
    "FlextInfraRefactorMROMigrationValidator",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorMROResolver",
    "FlextInfraRefactorMigrateToClassMRO",
    "FlextInfraRefactorRule",
    "FlextInfraRefactorRuleDefinitionValidator",
    "FlextInfraRefactorRuleLoader",
    "FlextInfraRefactorSafetyManager",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorTier0ImportFixRule",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
    "FlextInfraRefactorViolationAnalyzer",
    "census",
    "class_nesting_analyzer",
    "cli",
    "engine",
    "migrate_to_class_mro",
    "mro_import_rewriter",
    "mro_migration_validator",
    "mro_resolver",
    "namespace_enforcer",
    "project_classifier",
    "rule",
    "rule_definition_validator",
    "safety",
    "scanner",
    "violation_analyzer",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
