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
        census,
        class_nesting_analyzer,
        cli,
        engine,
        migrate_to_class_mro,
        mro_import_rewriter,
        mro_migration_validator,
        mro_resolver,
        namespace_enforcer,
        project_classifier,
        rule,
        rule_definition_validator,
        safety,
        scanner,
        violation_analyzer,
    )
    from flext_infra.refactor.census import *
    from flext_infra.refactor.class_nesting_analyzer import *
    from flext_infra.refactor.cli import *
    from flext_infra.refactor.engine import *
    from flext_infra.refactor.migrate_to_class_mro import *
    from flext_infra.refactor.mro_import_rewriter import *
    from flext_infra.refactor.mro_migration_validator import *
    from flext_infra.refactor.mro_resolver import *
    from flext_infra.refactor.namespace_enforcer import *
    from flext_infra.refactor.project_classifier import *
    from flext_infra.refactor.rule import *
    from flext_infra.refactor.rule_definition_validator import *
    from flext_infra.refactor.safety import *
    from flext_infra.refactor.scanner import *
    from flext_infra.refactor.violation_analyzer import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliRefactor": "flext_infra.refactor.cli",
    "FlextInfraNamespaceEnforcer": "flext_infra.refactor.namespace_enforcer",
    "FlextInfraProjectClassifier": "flext_infra.refactor.project_classifier",
    "FlextInfraRefactorCensus": "flext_infra.refactor.census",
    "FlextInfraRefactorClassNestingAnalyzer": "flext_infra.refactor.class_nesting_analyzer",
    "FlextInfraRefactorClassReconstructorRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorEngine": "flext_infra.refactor.engine",
    "FlextInfraRefactorLooseClassScanner": "flext_infra.refactor.scanner",
    "FlextInfraRefactorMROImportRewriter": "flext_infra.refactor.mro_import_rewriter",
    "FlextInfraRefactorMROMigrationValidator": "flext_infra.refactor.mro_migration_validator",
    "FlextInfraRefactorMRORedundancyChecker": "flext_infra.refactor.engine",
    "FlextInfraRefactorMROResolver": "flext_infra.refactor.mro_resolver",
    "FlextInfraRefactorMigrateToClassMRO": "flext_infra.refactor.migrate_to_class_mro",
    "FlextInfraRefactorRule": "flext_infra.refactor.rule",
    "FlextInfraRefactorRuleDefinitionValidator": "flext_infra.refactor.rule_definition_validator",
    "FlextInfraRefactorRuleLoader": "flext_infra.refactor.rule",
    "FlextInfraRefactorSafetyManager": "flext_infra.refactor.safety",
    "FlextInfraRefactorSignaturePropagationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorSymbolPropagationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTier0ImportFixRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTypingAnnotationFixRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTypingUnificationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorViolationAnalyzer": "flext_infra.refactor.violation_analyzer",
    "census": "flext_infra.refactor.census",
    "class_nesting_analyzer": "flext_infra.refactor.class_nesting_analyzer",
    "cli": "flext_infra.refactor.cli",
    "engine": "flext_infra.refactor.engine",
    "migrate_to_class_mro": "flext_infra.refactor.migrate_to_class_mro",
    "mro_import_rewriter": "flext_infra.refactor.mro_import_rewriter",
    "mro_migration_validator": "flext_infra.refactor.mro_migration_validator",
    "mro_resolver": "flext_infra.refactor.mro_resolver",
    "namespace_enforcer": "flext_infra.refactor.namespace_enforcer",
    "project_classifier": "flext_infra.refactor.project_classifier",
    "rule": "flext_infra.refactor.rule",
    "rule_definition_validator": "flext_infra.refactor.rule_definition_validator",
    "safety": "flext_infra.refactor.safety",
    "scanner": "flext_infra.refactor.scanner",
    "violation_analyzer": "flext_infra.refactor.violation_analyzer",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
