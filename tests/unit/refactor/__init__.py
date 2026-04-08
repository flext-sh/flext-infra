# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "test_infra_refactor_class_and_propagation": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_infra_refactor_class_placement": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_infra_refactor_cli_models_workflow": "tests.unit.refactor.test_infra_refactor_cli_models_workflow",
    "test_infra_refactor_engine": "tests.unit.refactor.test_infra_refactor_engine",
    "test_infra_refactor_import_modernizer": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_infra_refactor_legacy_and_annotations": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_infra_refactor_migrate_to_class_mro": "tests.unit.refactor.test_infra_refactor_migrate_to_class_mro",
    "test_infra_refactor_mro_completeness": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_infra_refactor_mro_import_rewriter": "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
    "test_infra_refactor_namespace_aliases": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_infra_refactor_namespace_enforcer": "tests.unit.refactor.test_infra_refactor_namespace_enforcer",
    "test_infra_refactor_namespace_moves": "tests.unit.refactor.test_infra_refactor_namespace_moves",
    "test_infra_refactor_namespace_source": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_infra_refactor_pattern_corrections": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_infra_refactor_policy_family_rules": "tests.unit.refactor.test_infra_refactor_policy_family_rules",
    "test_infra_refactor_project_classifier": "tests.unit.refactor.test_infra_refactor_project_classifier",
    "test_infra_refactor_safety": "tests.unit.refactor.test_infra_refactor_safety",
    "test_infra_refactor_typing_unifier": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_main_cli": "tests.unit.refactor.test_main_cli",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
