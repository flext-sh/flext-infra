# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_accessor_migration": ("TestsFlextInfraRefactorAccessorMigration",),
        ".test_infra_refactor_class_and_propagation": (
            "TestsFlextInfraRefactorInfraRefactorClassAndPropagation",
        ),
        ".test_infra_refactor_class_placement": (
            "TestsFlextInfraRefactorInfraRefactorClassPlacement",
        ),
        ".test_infra_refactor_cli_models_workflow": (
            "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
        ),
        ".test_infra_refactor_engine": ("TestsFlextInfraRefactorInfraRefactorEngine",),
        ".test_infra_refactor_import_modernizer": (
            "TestsFlextInfraRefactorInfraRefactorImportModernizer",
        ),
        ".test_infra_refactor_legacy_and_annotations": (
            "TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations",
        ),
        ".test_infra_refactor_migrate_to_class_mro": (
            "TestsFlextInfraRefactorInfraRefactorMigrateToClassMro",
        ),
        ".test_infra_refactor_mro_completeness": (
            "TestsFlextInfraRefactorInfraRefactorMroCompleteness",
        ),
        ".test_infra_refactor_mro_import_rewriter": (
            "test_infra_refactor_mro_import_rewriter",
        ),
        ".test_infra_refactor_namespace_aliases": (
            "TestsFlextInfraRefactorInfraRefactorNamespaceAliases",
        ),
        ".test_infra_refactor_namespace_enforcer": (
            "TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer",
        ),
        ".test_infra_refactor_namespace_moves": (
            "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
        ),
        ".test_infra_refactor_pattern_corrections": (
            "TestsFlextInfraRefactorInfraRefactorPatternCorrections",
        ),
        ".test_infra_refactor_policy_family_rules": (
            "TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules",
        ),
        ".test_infra_refactor_project_classifier": (
            "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
        ),
        ".test_infra_refactor_safety": (
            "EngineSafetyStub",
            "TestsFlextInfraRefactorInfraRefactorSafety",
        ),
        ".test_infra_refactor_typing_unifier": (
            "FlextInfraRefactorTypingUnificationRule",
            "TestsFlextInfraRefactorInfraRefactorTypingUnifier",
        ),
        ".test_main_cli": ("TestsFlextInfraRefactorMainCli",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
