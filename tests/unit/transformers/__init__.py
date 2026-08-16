# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.transformers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_infra_transformer_cast_remover import (
        TestsFlextInfraTransformersCastRemover,
    )
    from .test_infra_transformer_class_nesting import (
        TestsFlextInfraTransformersInfraTransformerClassNesting,
    )
    from .test_infra_transformer_cli_modernizer import (
        TestsFlextInfraTransformersCliModernizer,
    )
    from .test_infra_transformer_enforcement_fixers import (
        TestsFlextInfraTransformersCompatibilityAlias,
        TestsFlextInfraTransformersFutureImport,
        TestsFlextInfraTransformersHardcodedVersion,
        TestsFlextInfraTransformersOpenEncoding,
        TestsFlextInfraTransformersPattern,
        TestsFlextInfraTransformersPatternList,
        TestsFlextInfraTransformersPatternStructlog,
        TestsFlextInfraTransformersTypingDictAttr,
        TestsFlextInfraTransformersTypingDictImport,
        TestsFlextInfraTransformersTypingUnifier,
    )
    from .test_infra_transformer_helper_consolidation import (
        TestsFlextInfraTransformersInfraTransformerHelperConsolidation,
    )
    from .test_infra_transformer_logging_modernizer import (
        TestsFlextInfraTransformersLoggingModernizer,
    )
    from .test_infra_transformer_nested_class_propagation import (
        TestsFlextInfraTransformersInfraTransformerNestedClassPropagation,
    )
    from .test_infra_transformer_pattern_modernizer import (
        TestsFlextInfraTransformersPatternModernizer,
    )
    from .test_infra_transformer_pydantic_modernizer import (
        TestsFlextInfraTransformersPydanticModernizer,
    )
    from .test_infra_transformer_result_di_modernizer import (
        TestsFlextInfraTransformersResultDiModernizer,
    )
    from .test_project_alias_migrator import TestsFlextInfraRefactorProjectAliasMigrator
__all__: tuple[str, ...] = (
    "TestsFlextInfraRefactorProjectAliasMigrator",
    "TestsFlextInfraTransformersCastRemover",
    "TestsFlextInfraTransformersCliModernizer",
    "TestsFlextInfraTransformersCompatibilityAlias",
    "TestsFlextInfraTransformersFutureImport",
    "TestsFlextInfraTransformersHardcodedVersion",
    "TestsFlextInfraTransformersInfraTransformerClassNesting",
    "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
    "TestsFlextInfraTransformersInfraTransformerNestedClassPropagation",
    "TestsFlextInfraTransformersLoggingModernizer",
    "TestsFlextInfraTransformersOpenEncoding",
    "TestsFlextInfraTransformersPattern",
    "TestsFlextInfraTransformersPatternList",
    "TestsFlextInfraTransformersPatternModernizer",
    "TestsFlextInfraTransformersPatternStructlog",
    "TestsFlextInfraTransformersPydanticModernizer",
    "TestsFlextInfraTransformersResultDiModernizer",
    "TestsFlextInfraTransformersTypingDictAttr",
    "TestsFlextInfraTransformersTypingDictImport",
    "TestsFlextInfraTransformersTypingUnifier",
    "c",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".test_infra_transformer_cast_remover": (
                    "TestsFlextInfraTransformersCastRemover",
                ),
                ".test_infra_transformer_class_nesting": (
                    "TestsFlextInfraTransformersInfraTransformerClassNesting",
                ),
                ".test_infra_transformer_cli_modernizer": (
                    "TestsFlextInfraTransformersCliModernizer",
                ),
                ".test_infra_transformer_enforcement_fixers": (
                    "TestsFlextInfraTransformersCompatibilityAlias",
                    "TestsFlextInfraTransformersFutureImport",
                    "TestsFlextInfraTransformersHardcodedVersion",
                    "TestsFlextInfraTransformersOpenEncoding",
                    "TestsFlextInfraTransformersPattern",
                    "TestsFlextInfraTransformersPatternList",
                    "TestsFlextInfraTransformersPatternStructlog",
                    "TestsFlextInfraTransformersTypingDictAttr",
                    "TestsFlextInfraTransformersTypingDictImport",
                    "TestsFlextInfraTransformersTypingUnifier",
                ),
                ".test_infra_transformer_helper_consolidation": (
                    "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
                ),
                ".test_infra_transformer_logging_modernizer": (
                    "TestsFlextInfraTransformersLoggingModernizer",
                ),
                ".test_infra_transformer_nested_class_propagation": (
                    "TestsFlextInfraTransformersInfraTransformerNestedClassPropagation",
                ),
                ".test_infra_transformer_pattern_modernizer": (
                    "TestsFlextInfraTransformersPatternModernizer",
                ),
                ".test_infra_transformer_pydantic_modernizer": (
                    "TestsFlextInfraTransformersPydanticModernizer",
                ),
                ".test_infra_transformer_result_di_modernizer": (
                    "TestsFlextInfraTransformersResultDiModernizer",
                ),
                ".test_project_alias_migrator": (
                    "TestsFlextInfraRefactorProjectAliasMigrator",
                ),
                "flext_tests": (
                    "c",
                    "d",
                    "e",
                    "h",
                    "m",
                    "p",
                    "r",
                    "s",
                    "t",
                    "td",
                    "tf",
                    "tk",
                    "tm",
                    "tv",
                    "u",
                    "x",
                ),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
