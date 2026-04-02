# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Public API for flext_infra.refactor with lazy loading."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.refactor import (
        _base_rule,
        _constants,
        _models,
        _models_ast_grep,
        _models_namespace_enforcer,
        _post_check_gate,
        _utilities,
        _utilities_cli,
        _utilities_loader,
        _utilities_mro_scan,
        _utilities_mro_transform,
        _utilities_namespace,
        _utilities_pydantic,
        _utilities_pydantic_analysis,
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
    from flext_infra.refactor._base_rule import (
        CONTAINER_DICT_SEQ_ADAPTER,
        INFRA_MAPPING_ADAPTER,
        INFRA_SEQ_ADAPTER,
        STR_MAPPING_ADAPTER,
        FlextInfraChangeTracker,
        FlextInfraGenericTransformerRule,
        FlextInfraRefactorRule,
    )
    from flext_infra.refactor._constants import FlextInfraRefactorConstants
    from flext_infra.refactor._models import FlextInfraRefactorModels
    from flext_infra.refactor._models_ast_grep import FlextInfraRefactorAstGrepModels
    from flext_infra.refactor._models_namespace_enforcer import (
        FlextInfraNamespaceEnforcerModels,
    )
    from flext_infra.refactor._post_check_gate import FlextInfraPostCheckGate
    from flext_infra.refactor._utilities import FlextInfraUtilitiesRefactor
    from flext_infra.refactor._utilities_cli import FlextInfraUtilitiesRefactorCli
    from flext_infra.refactor._utilities_loader import FlextInfraUtilitiesRefactorLoader
    from flext_infra.refactor._utilities_mro_scan import (
        FlextInfraUtilitiesRefactorMroScan,
    )
    from flext_infra.refactor._utilities_mro_transform import (
        FlextInfraUtilitiesRefactorMroTransform,
    )
    from flext_infra.refactor._utilities_namespace import (
        FlextInfraUtilitiesRefactorNamespace,
    )
    from flext_infra.refactor._utilities_pydantic import (
        FlextInfraUtilitiesRefactorPydantic,
    )
    from flext_infra.refactor._utilities_pydantic_analysis import (
        FlextInfraUtilitiesRefactorPydanticAnalysis,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.class_nesting_analyzer import (
        FlextInfraRefactorClassNestingAnalyzer,
    )
    from flext_infra.refactor.cli import FlextInfraCliRefactor
    from flext_infra.refactor.engine import (
        FlextInfraRefactorClassReconstructorRule,
        FlextInfraRefactorEngine,
        FlextInfraRefactorMRORedundancyChecker,
        FlextInfraRefactorSignaturePropagationRule,
        FlextInfraRefactorSymbolPropagationRule,
        FlextInfraRefactorTier0ImportFixRule,
        FlextInfraRefactorTypingAnnotationFixRule,
        FlextInfraRefactorTypingUnificationRule,
    )
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
    from flext_infra.refactor.rule import FlextInfraRefactorRuleLoader
    from flext_infra.refactor.rule_definition_validator import (
        FlextInfraRefactorRuleDefinitionValidator,
    )
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
    from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
    from flext_infra.refactor.violation_analyzer import (
        FlextInfraRefactorViolationAnalyzer,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "CONTAINER_DICT_SEQ_ADAPTER": "flext_infra.refactor._base_rule",
    "FlextInfraChangeTracker": "flext_infra.refactor._base_rule",
    "FlextInfraCliRefactor": "flext_infra.refactor.cli",
    "FlextInfraGenericTransformerRule": "flext_infra.refactor._base_rule",
    "FlextInfraNamespaceEnforcer": "flext_infra.refactor.namespace_enforcer",
    "FlextInfraNamespaceEnforcerModels": "flext_infra.refactor._models_namespace_enforcer",
    "FlextInfraPostCheckGate": "flext_infra.refactor._post_check_gate",
    "FlextInfraProjectClassifier": "flext_infra.refactor.project_classifier",
    "FlextInfraRefactorAstGrepModels": "flext_infra.refactor._models_ast_grep",
    "FlextInfraRefactorCensus": "flext_infra.refactor.census",
    "FlextInfraRefactorClassNestingAnalyzer": "flext_infra.refactor.class_nesting_analyzer",
    "FlextInfraRefactorClassReconstructorRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorConstants": "flext_infra.refactor._constants",
    "FlextInfraRefactorEngine": "flext_infra.refactor.engine",
    "FlextInfraRefactorLooseClassScanner": "flext_infra.refactor.scanner",
    "FlextInfraRefactorMROImportRewriter": "flext_infra.refactor.mro_import_rewriter",
    "FlextInfraRefactorMROMigrationValidator": "flext_infra.refactor.mro_migration_validator",
    "FlextInfraRefactorMRORedundancyChecker": "flext_infra.refactor.engine",
    "FlextInfraRefactorMROResolver": "flext_infra.refactor.mro_resolver",
    "FlextInfraRefactorMigrateToClassMRO": "flext_infra.refactor.migrate_to_class_mro",
    "FlextInfraRefactorModels": "flext_infra.refactor._models",
    "FlextInfraRefactorRule": "flext_infra.refactor._base_rule",
    "FlextInfraRefactorRuleDefinitionValidator": "flext_infra.refactor.rule_definition_validator",
    "FlextInfraRefactorRuleLoader": "flext_infra.refactor.rule",
    "FlextInfraRefactorSafetyManager": "flext_infra.refactor.safety",
    "FlextInfraRefactorSignaturePropagationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorSymbolPropagationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTier0ImportFixRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTypingAnnotationFixRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorTypingUnificationRule": "flext_infra.refactor.engine",
    "FlextInfraRefactorViolationAnalyzer": "flext_infra.refactor.violation_analyzer",
    "FlextInfraUtilitiesRefactor": "flext_infra.refactor._utilities",
    "FlextInfraUtilitiesRefactorCli": "flext_infra.refactor._utilities_cli",
    "FlextInfraUtilitiesRefactorLoader": "flext_infra.refactor._utilities_loader",
    "FlextInfraUtilitiesRefactorMroScan": "flext_infra.refactor._utilities_mro_scan",
    "FlextInfraUtilitiesRefactorMroTransform": "flext_infra.refactor._utilities_mro_transform",
    "FlextInfraUtilitiesRefactorNamespace": "flext_infra.refactor._utilities_namespace",
    "FlextInfraUtilitiesRefactorPydantic": "flext_infra.refactor._utilities_pydantic",
    "FlextInfraUtilitiesRefactorPydanticAnalysis": "flext_infra.refactor._utilities_pydantic_analysis",
    "INFRA_MAPPING_ADAPTER": "flext_infra.refactor._base_rule",
    "INFRA_SEQ_ADAPTER": "flext_infra.refactor._base_rule",
    "STR_MAPPING_ADAPTER": "flext_infra.refactor._base_rule",
    "_base_rule": "flext_infra.refactor._base_rule",
    "_constants": "flext_infra.refactor._constants",
    "_models": "flext_infra.refactor._models",
    "_models_ast_grep": "flext_infra.refactor._models_ast_grep",
    "_models_namespace_enforcer": "flext_infra.refactor._models_namespace_enforcer",
    "_post_check_gate": "flext_infra.refactor._post_check_gate",
    "_utilities": "flext_infra.refactor._utilities",
    "_utilities_cli": "flext_infra.refactor._utilities_cli",
    "_utilities_loader": "flext_infra.refactor._utilities_loader",
    "_utilities_mro_scan": "flext_infra.refactor._utilities_mro_scan",
    "_utilities_mro_transform": "flext_infra.refactor._utilities_mro_transform",
    "_utilities_namespace": "flext_infra.refactor._utilities_namespace",
    "_utilities_pydantic": "flext_infra.refactor._utilities_pydantic",
    "_utilities_pydantic_analysis": "flext_infra.refactor._utilities_pydantic_analysis",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
