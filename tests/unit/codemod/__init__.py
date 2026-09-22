# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codemod package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_api_alias_cutover import TestsFlextInfraApiAliasCutover
    from .test_apply_renames import TestsFlextInfraApplyRenames
    from .test_batch_apply_validation import TestsFlextInfraCodemodBatchApplyValidation
    from .test_family_flatten import TestsFlextInfraFamilyFlatten
    from .test_mod_circuit import TestsFlextInfraModCliRoute
    from .test_mod_text_circuit import TestsFlextInfraModTextGateEngine
    from .test_nesting_cst_output_is_clean import TestsFlextInfraNestingCutoverOutput
    from .test_private_import_cutover import TestsFlextInfraPrivateImportCutover
    from .test_rule_expected_receipt import TestsFlextInfraModRuleExpectedReceipt
    from .test_rule_fixture_staging import TestsFlextInfraModRuleFixtureStaging
    from .test_semantic_publication import TestsSemanticPublication


__all__: tuple[str, ...] = (
    "TestsFlextInfraApiAliasCutover",
    "TestsFlextInfraApplyRenames",
    "TestsFlextInfraCodemodBatchApplyValidation",
    "TestsFlextInfraFamilyFlatten",
    "TestsFlextInfraModCliRoute",
    "TestsFlextInfraModRuleExpectedReceipt",
    "TestsFlextInfraModRuleFixtureStaging",
    "TestsFlextInfraModTextGateEngine",
    "TestsFlextInfraNestingCutoverOutput",
    "TestsFlextInfraPrivateImportCutover",
    "TestsSemanticPublication",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_api_alias_cutover": ("TestsFlextInfraApiAliasCutover",),
            ".test_apply_renames": ("TestsFlextInfraApplyRenames",),
            ".test_batch_apply_validation": (
                "TestsFlextInfraCodemodBatchApplyValidation",
            ),
            ".test_family_flatten": ("TestsFlextInfraFamilyFlatten",),
            ".test_mod_circuit": ("TestsFlextInfraModCliRoute",),
            ".test_mod_text_circuit": ("TestsFlextInfraModTextGateEngine",),
            ".test_nesting_cst_output_is_clean": (
                "TestsFlextInfraNestingCutoverOutput",
            ),
            ".test_private_import_cutover": ("TestsFlextInfraPrivateImportCutover",),
            ".test_rule_expected_receipt": ("TestsFlextInfraModRuleExpectedReceipt",),
            ".test_rule_fixture_staging": ("TestsFlextInfraModRuleFixtureStaging",),
            ".test_semantic_publication": ("TestsSemanticPublication",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
