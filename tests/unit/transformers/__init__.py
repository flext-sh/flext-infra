# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.transformers package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_infra_transformer_cast_remover import (
        TestsFlextInfraCastRemoverDeactivated,
    )
    from .test_infra_transformer_enforcement_fixers import (
        TestsFlextInfraTransformersEnforcementFixers,
    )
    from .test_infra_transformer_mro_remover import (
        TestsFlextInfraTransformersMroRemover,
    )
    from .test_infra_transformer_pydantic_modernizer import (
        TestsFlextInfraTransformersPydanticModernizer,
    )
    from .test_infra_transformer_typing_dict import TestsFlextInfraTypingDictDeactivated
    from .test_project_alias_migrator import TestsFlextInfraRefactorProjectAliasMigrator
__all__: tuple[str, ...] = (
    "TestsFlextInfraCastRemoverDeactivated",
    "TestsFlextInfraRefactorProjectAliasMigrator",
    "TestsFlextInfraTransformersEnforcementFixers",
    "TestsFlextInfraTransformersMroRemover",
    "TestsFlextInfraTransformersPydanticModernizer",
    "TestsFlextInfraTypingDictDeactivated",
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

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_infra_transformer_cast_remover": (
                "TestsFlextInfraCastRemoverDeactivated",
            ),
            ".test_infra_transformer_enforcement_fixers": (
                "TestsFlextInfraTransformersEnforcementFixers",
            ),
            ".test_infra_transformer_mro_remover": (
                "TestsFlextInfraTransformersMroRemover",
            ),
            ".test_infra_transformer_pydantic_modernizer": (
                "TestsFlextInfraTransformersPydanticModernizer",
            ),
            ".test_infra_transformer_typing_dict": (
                "TestsFlextInfraTypingDictDeactivated",
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
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
