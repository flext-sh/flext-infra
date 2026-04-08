# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Transformers package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.transformers.test_infra_transformer_class_nesting as _tests_unit_transformers_test_infra_transformer_class_nesting

    test_infra_transformer_class_nesting = (
        _tests_unit_transformers_test_infra_transformer_class_nesting
    )
    import tests.unit.transformers.test_infra_transformer_helper_consolidation as _tests_unit_transformers_test_infra_transformer_helper_consolidation
    from tests.unit.transformers.test_infra_transformer_class_nesting import (
        test_class_nesting_appends_to_existing_namespace_and_removes_pass,
        test_class_nesting_keeps_unmapped_top_level_classes,
        test_class_nesting_moves_top_level_class_into_new_namespace,
    )

    test_infra_transformer_helper_consolidation = (
        _tests_unit_transformers_test_infra_transformer_helper_consolidation
    )
    import tests.unit.transformers.test_infra_transformer_nested_class_propagation as _tests_unit_transformers_test_infra_transformer_nested_class_propagation
    from tests.unit.transformers.test_infra_transformer_helper_consolidation import (
        TestHelperConsolidationTransformer,
    )

    test_infra_transformer_nested_class_propagation = (
        _tests_unit_transformers_test_infra_transformer_nested_class_propagation
    )
    from tests.unit.transformers.test_infra_transformer_nested_class_propagation import (
        test_nested_class_propagation_preserves_asname_and_rewrites_alias_usage,
        test_nested_class_propagation_updates_import_annotations_and_calls,
    )

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "TestHelperConsolidationTransformer": (
        "tests.unit.transformers.test_infra_transformer_helper_consolidation",
        "TestHelperConsolidationTransformer",
    ),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "test_class_nesting_appends_to_existing_namespace_and_removes_pass": (
        "tests.unit.transformers.test_infra_transformer_class_nesting",
        "test_class_nesting_appends_to_existing_namespace_and_removes_pass",
    ),
    "test_class_nesting_keeps_unmapped_top_level_classes": (
        "tests.unit.transformers.test_infra_transformer_class_nesting",
        "test_class_nesting_keeps_unmapped_top_level_classes",
    ),
    "test_class_nesting_moves_top_level_class_into_new_namespace": (
        "tests.unit.transformers.test_infra_transformer_class_nesting",
        "test_class_nesting_moves_top_level_class_into_new_namespace",
    ),
    "test_infra_transformer_class_nesting": "tests.unit.transformers.test_infra_transformer_class_nesting",
    "test_infra_transformer_helper_consolidation": "tests.unit.transformers.test_infra_transformer_helper_consolidation",
    "test_infra_transformer_nested_class_propagation": "tests.unit.transformers.test_infra_transformer_nested_class_propagation",
    "test_nested_class_propagation_preserves_asname_and_rewrites_alias_usage": (
        "tests.unit.transformers.test_infra_transformer_nested_class_propagation",
        "test_nested_class_propagation_preserves_asname_and_rewrites_alias_usage",
    ),
    "test_nested_class_propagation_updates_import_annotations_and_calls": (
        "tests.unit.transformers.test_infra_transformer_nested_class_propagation",
        "test_nested_class_propagation_updates_import_annotations_and_calls",
    ),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "TestHelperConsolidationTransformer",
    "d",
    "e",
    "h",
    "r",
    "s",
    "test_class_nesting_appends_to_existing_namespace_and_removes_pass",
    "test_class_nesting_keeps_unmapped_top_level_classes",
    "test_class_nesting_moves_top_level_class_into_new_namespace",
    "test_infra_transformer_class_nesting",
    "test_infra_transformer_helper_consolidation",
    "test_infra_transformer_nested_class_propagation",
    "test_nested_class_propagation_preserves_asname_and_rewrites_alias_usage",
    "test_nested_class_propagation_updates_import_annotations_and_calls",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
