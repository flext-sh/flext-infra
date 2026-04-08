# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.refactor.test_infra_refactor_class_and_propagation as _tests_unit_refactor_test_infra_refactor_class_and_propagation

    test_infra_refactor_class_and_propagation = (
        _tests_unit_refactor_test_infra_refactor_class_and_propagation
    )
    import tests.unit.refactor.test_infra_refactor_class_placement as _tests_unit_refactor_test_infra_refactor_class_placement

    test_infra_refactor_class_placement = (
        _tests_unit_refactor_test_infra_refactor_class_placement
    )
    import tests.unit.refactor.test_infra_refactor_cli_models_workflow as _tests_unit_refactor_test_infra_refactor_cli_models_workflow

    test_infra_refactor_cli_models_workflow = (
        _tests_unit_refactor_test_infra_refactor_cli_models_workflow
    )
    import tests.unit.refactor.test_infra_refactor_engine as _tests_unit_refactor_test_infra_refactor_engine

    test_infra_refactor_engine = _tests_unit_refactor_test_infra_refactor_engine
    import tests.unit.refactor.test_infra_refactor_import_modernizer as _tests_unit_refactor_test_infra_refactor_import_modernizer
    from tests.unit.refactor.test_infra_refactor_engine import BrokenRule

    test_infra_refactor_import_modernizer = (
        _tests_unit_refactor_test_infra_refactor_import_modernizer
    )
    import tests.unit.refactor.test_infra_refactor_legacy_and_annotations as _tests_unit_refactor_test_infra_refactor_legacy_and_annotations

    test_infra_refactor_legacy_and_annotations = (
        _tests_unit_refactor_test_infra_refactor_legacy_and_annotations
    )
    import tests.unit.refactor.test_infra_refactor_migrate_to_class_mro as _tests_unit_refactor_test_infra_refactor_migrate_to_class_mro

    test_infra_refactor_migrate_to_class_mro = (
        _tests_unit_refactor_test_infra_refactor_migrate_to_class_mro
    )
    import tests.unit.refactor.test_infra_refactor_mro_completeness as _tests_unit_refactor_test_infra_refactor_mro_completeness

    test_infra_refactor_mro_completeness = (
        _tests_unit_refactor_test_infra_refactor_mro_completeness
    )
    import tests.unit.refactor.test_infra_refactor_mro_import_rewriter as _tests_unit_refactor_test_infra_refactor_mro_import_rewriter

    test_infra_refactor_mro_import_rewriter = (
        _tests_unit_refactor_test_infra_refactor_mro_import_rewriter
    )
    import tests.unit.refactor.test_infra_refactor_namespace_aliases as _tests_unit_refactor_test_infra_refactor_namespace_aliases

    test_infra_refactor_namespace_aliases = (
        _tests_unit_refactor_test_infra_refactor_namespace_aliases
    )
    import tests.unit.refactor.test_infra_refactor_namespace_enforcer as _tests_unit_refactor_test_infra_refactor_namespace_enforcer

    test_infra_refactor_namespace_enforcer = (
        _tests_unit_refactor_test_infra_refactor_namespace_enforcer
    )
    import tests.unit.refactor.test_infra_refactor_namespace_moves as _tests_unit_refactor_test_infra_refactor_namespace_moves

    test_infra_refactor_namespace_moves = (
        _tests_unit_refactor_test_infra_refactor_namespace_moves
    )
    import tests.unit.refactor.test_infra_refactor_namespace_source as _tests_unit_refactor_test_infra_refactor_namespace_source

    test_infra_refactor_namespace_source = (
        _tests_unit_refactor_test_infra_refactor_namespace_source
    )
    import tests.unit.refactor.test_infra_refactor_pattern_corrections as _tests_unit_refactor_test_infra_refactor_pattern_corrections
    from tests.unit.refactor.test_infra_refactor_namespace_source import (
        FAMILY_FILE_MAP,
        FAMILY_SUFFIX_MAP,
    )

    test_infra_refactor_pattern_corrections = (
        _tests_unit_refactor_test_infra_refactor_pattern_corrections
    )
    import tests.unit.refactor.test_infra_refactor_policy_family_rules as _tests_unit_refactor_test_infra_refactor_policy_family_rules

    test_infra_refactor_policy_family_rules = (
        _tests_unit_refactor_test_infra_refactor_policy_family_rules
    )
    import tests.unit.refactor.test_infra_refactor_project_classifier as _tests_unit_refactor_test_infra_refactor_project_classifier

    test_infra_refactor_project_classifier = (
        _tests_unit_refactor_test_infra_refactor_project_classifier
    )
    import tests.unit.refactor.test_infra_refactor_safety as _tests_unit_refactor_test_infra_refactor_safety

    test_infra_refactor_safety = _tests_unit_refactor_test_infra_refactor_safety
    import tests.unit.refactor.test_infra_refactor_typing_unifier as _tests_unit_refactor_test_infra_refactor_typing_unifier
    from tests.unit.refactor.test_infra_refactor_safety import EngineSafetyStub

    test_infra_refactor_typing_unifier = (
        _tests_unit_refactor_test_infra_refactor_typing_unifier
    )
    import tests.unit.refactor.test_main_cli as _tests_unit_refactor_test_main_cli

    test_main_cli = _tests_unit_refactor_test_main_cli
    from tests.unit.refactor.test_main_cli import refactor_main

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "BrokenRule": ("tests.unit.refactor.test_infra_refactor_engine", "BrokenRule"),
    "EngineSafetyStub": (
        "tests.unit.refactor.test_infra_refactor_safety",
        "EngineSafetyStub",
    ),
    "FAMILY_FILE_MAP": (
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_FILE_MAP",
    ),
    "FAMILY_SUFFIX_MAP": (
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_SUFFIX_MAP",
    ),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "refactor_main": ("tests.unit.refactor.test_main_cli", "refactor_main"),
    "s": ("flext_core.service", "FlextService"),
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
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
    "BrokenRule",
    "EngineSafetyStub",
    "d",
    "e",
    "h",
    "r",
    "refactor_main",
    "s",
    "test_infra_refactor_class_and_propagation",
    "test_infra_refactor_class_placement",
    "test_infra_refactor_cli_models_workflow",
    "test_infra_refactor_engine",
    "test_infra_refactor_import_modernizer",
    "test_infra_refactor_legacy_and_annotations",
    "test_infra_refactor_migrate_to_class_mro",
    "test_infra_refactor_mro_completeness",
    "test_infra_refactor_mro_import_rewriter",
    "test_infra_refactor_namespace_aliases",
    "test_infra_refactor_namespace_enforcer",
    "test_infra_refactor_namespace_moves",
    "test_infra_refactor_namespace_source",
    "test_infra_refactor_pattern_corrections",
    "test_infra_refactor_policy_family_rules",
    "test_infra_refactor_project_classifier",
    "test_infra_refactor_safety",
    "test_infra_refactor_typing_unifier",
    "test_main_cli",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
