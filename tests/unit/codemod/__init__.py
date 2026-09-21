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
    from .test_batch_replacements import TestsBatchReplacements
    from .test_mod_circuit import TestsFlextInfraModCliRoute
    from .test_mod_text_circuit import TestsFlextInfraModTextGateEngine
    from .test_nesting_cst_output_is_clean import TestsFlextInfraNestingCutoverOutput
    from .test_private_import_cutover import TestsFlextInfraPrivateImportCutover
    from .test_rule_expected_receipt import TestsFlextInfraModRuleExpectedReceipt
    from .test_rule_fixture_staging import TestsFlextInfraModRuleFixtureStaging
    from .test_semantic_phase_contract import TestsFlextInfraSemanticPhaseContract
__all__: tuple[str, ...] = (
    "TestsBatchReplacements", "TestsFlextInfraApiAliasCutover", "TestsFlextInfraCodemodBatchApplyValidation", "TestsFlextInfraModCliRoute",
    "TestsFlextInfraModRuleExpectedReceipt", "TestsFlextInfraModRuleFixtureStaging", "TestsFlextInfraModTextGateEngine", "TestsFlextInfraNestingCutoverOutput",
    "TestsFlextInfraPrivateImportCutover", "TestsFlextInfraSemanticPhaseContract", "c", "d",
    "e", "h", "m", "p",
    "r", "s", "t", "td",
    "tf", "tk", "tm", "tv",
    "u", "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_api_alias_cutover": ("TestsFlextInfraApiAliasCutover",),
            ".test_batch_apply_validation": (
                "TestsFlextInfraCodemodBatchApplyValidation",
            ),
            ".test_batch_replacements": ("TestsBatchReplacements",),
            ".test_mod_circuit": ("TestsFlextInfraModCliRoute",),
            ".test_mod_text_circuit": ("TestsFlextInfraModTextGateEngine",),
            ".test_nesting_cst_output_is_clean": (
                "TestsFlextInfraNestingCutoverOutput",
            ),
            ".test_private_import_cutover": ("TestsFlextInfraPrivateImportCutover",),
            ".test_rule_expected_receipt": ("TestsFlextInfraModRuleExpectedReceipt",),
            ".test_rule_fixture_staging": ("TestsFlextInfraModRuleFixtureStaging",),
            ".test_semantic_phase_contract": ("TestsFlextInfraSemanticPhaseContract",),
            "flext_tests": (
                "c", "d", "e", "h", "m", "p", "r", "s", "t", "td", "tf", "tk", "tm",
                "tv", "u", "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
