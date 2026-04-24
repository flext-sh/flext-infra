# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_accessor_migration": ("test_accessor_migration",),
        ".test_infra_refactor_class_and_propagation": (
            "test_infra_refactor_class_and_propagation",
        ),
        ".test_infra_refactor_class_placement": (
            "test_infra_refactor_class_placement",
        ),
        ".test_infra_refactor_cli_models_workflow": (
            "test_infra_refactor_cli_models_workflow",
        ),
        ".test_infra_refactor_engine": ("test_infra_refactor_engine",),
        ".test_infra_refactor_import_modernizer": (
            "test_infra_refactor_import_modernizer",
        ),
        ".test_infra_refactor_legacy_and_annotations": (
            "test_infra_refactor_legacy_and_annotations",
        ),
        ".test_infra_refactor_migrate_to_class_mro": (
            "test_infra_refactor_migrate_to_class_mro",
        ),
        ".test_infra_refactor_mro_completeness": (
            "test_infra_refactor_mro_completeness",
        ),
        ".test_infra_refactor_mro_import_rewriter": (
            "test_infra_refactor_mro_import_rewriter",
        ),
        ".test_infra_refactor_namespace_aliases": (
            "test_infra_refactor_namespace_aliases",
        ),
        ".test_infra_refactor_namespace_enforcer": (
            "test_infra_refactor_namespace_enforcer",
        ),
        ".test_infra_refactor_namespace_moves": (
            "test_infra_refactor_namespace_moves",
        ),
        ".test_infra_refactor_pattern_corrections": (
            "test_infra_refactor_pattern_corrections",
        ),
        ".test_infra_refactor_policy_family_rules": (
            "test_infra_refactor_policy_family_rules",
        ),
        ".test_infra_refactor_project_classifier": (
            "test_infra_refactor_project_classifier",
        ),
        ".test_infra_refactor_safety": ("EngineSafetyStub",),
        ".test_infra_refactor_typing_unifier": (
            "FlextInfraRefactorTypingUnificationRule",
        ),
        ".test_main_cli": ("TestFlextInfraRefactorMainCli",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
