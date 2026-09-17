# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codemod package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_api_alias_cutover import TestsFlextInfraApiAliasCutover
    from .test_batch_apply_validation import TestsFlextInfraCodemodBatchApplyValidation
    from .test_mod_circuit import TestsFlextInfraModCliRoute
    from .test_mod_text_circuit import TestsFlextInfraModTextGateEngine
    from .test_private_import_cutover import TestsFlextInfraPrivateImportCutover
    from .test_rule_fixture_staging import TestsFlextInfraModRuleFixtureStaging
__all__: tuple[str, ...] = (
    "TestsFlextInfraApiAliasCutover",
    "TestsFlextInfraCodemodBatchApplyValidation",
    "TestsFlextInfraModCliRoute",
    "TestsFlextInfraModRuleFixtureStaging",
    "TestsFlextInfraModTextGateEngine",
    "TestsFlextInfraPrivateImportCutover",
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
            ".test_api_alias_cutover": ("TestsFlextInfraApiAliasCutover",),
            ".test_batch_apply_validation": (
                "TestsFlextInfraCodemodBatchApplyValidation",
            ),
            ".test_mod_circuit": ("TestsFlextInfraModCliRoute",),
            ".test_mod_text_circuit": ("TestsFlextInfraModTextGateEngine",),
            ".test_private_import_cutover": ("TestsFlextInfraPrivateImportCutover",),
            ".test_rule_fixture_staging": ("TestsFlextInfraModRuleFixtureStaging",),
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
