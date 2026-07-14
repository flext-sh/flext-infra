# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.transformers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.transformers.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u,
        x as x,
    )

    from tests.unit.transformers.test_infra_transformer_cast_remover import (
        TestsFlextInfraTransformersCastRemover as TestsFlextInfraTransformersCastRemover,
    )
    from tests.unit.transformers.test_infra_transformer_class_nesting import (
        TestsFlextInfraTransformersInfraTransformerClassNesting as TestsFlextInfraTransformersInfraTransformerClassNesting,
    )
    from tests.unit.transformers.test_infra_transformer_cli_modernizer import (
        TestsFlextInfraTransformersCliModernizer as TestsFlextInfraTransformersCliModernizer,
    )
    from tests.unit.transformers.test_infra_transformer_enforcement_fixers import (
        TestsFlextInfraTransformersCompatibilityAlias as TestsFlextInfraTransformersCompatibilityAlias,
        TestsFlextInfraTransformersFutureImport as TestsFlextInfraTransformersFutureImport,
        TestsFlextInfraTransformersHardcodedVersion as TestsFlextInfraTransformersHardcodedVersion,
        TestsFlextInfraTransformersOpenEncoding as TestsFlextInfraTransformersOpenEncoding,
        TestsFlextInfraTransformersPattern as TestsFlextInfraTransformersPattern,
        TestsFlextInfraTransformersPatternList as TestsFlextInfraTransformersPatternList,
        TestsFlextInfraTransformersPatternStructlog as TestsFlextInfraTransformersPatternStructlog,
        TestsFlextInfraTransformersTypingDictAttr as TestsFlextInfraTransformersTypingDictAttr,
        TestsFlextInfraTransformersTypingDictImport as TestsFlextInfraTransformersTypingDictImport,
        TestsFlextInfraTransformersTypingUnifier as TestsFlextInfraTransformersTypingUnifier,
    )
    from tests.unit.transformers.test_infra_transformer_helper_consolidation import (
        TestsFlextInfraTransformersInfraTransformerHelperConsolidation as TestsFlextInfraTransformersInfraTransformerHelperConsolidation,
    )
    from tests.unit.transformers.test_infra_transformer_logging_modernizer import (
        TestsFlextInfraTransformersLoggingModernizer as TestsFlextInfraTransformersLoggingModernizer,
    )
    from tests.unit.transformers.test_infra_transformer_nested_class_propagation import (
        TestsFlextInfraTransformersInfraTransformerNestedClassPropagation as TestsFlextInfraTransformersInfraTransformerNestedClassPropagation,
    )
    from tests.unit.transformers.test_infra_transformer_pattern_modernizer import (
        TestsFlextInfraTransformersPatternModernizer as TestsFlextInfraTransformersPatternModernizer,
    )
    from tests.unit.transformers.test_infra_transformer_pydantic_modernizer import (
        TestsFlextInfraTransformersPydanticModernizer as TestsFlextInfraTransformersPydanticModernizer,
    )
    from tests.unit.transformers.test_infra_transformer_result_di_modernizer import (
        TestsFlextInfraTransformersResultDiModernizer as TestsFlextInfraTransformersResultDiModernizer,
    )
    from tests.unit.transformers.test_infra_transformer_tests_modernizer import (
        TestsFlextInfraTransformersTestsModernizer as TestsFlextInfraTransformersTestsModernizer,
    )
    from tests.unit.transformers.test_project_alias_migrator import (
        TestsFlextInfraRefactorProjectAliasMigrator as TestsFlextInfraRefactorProjectAliasMigrator,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
