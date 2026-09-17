# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.validate package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .fresh_import_tests import TestsFlextInfraFreshImport
    from .governance_authority_tests import TestsFlextInfraGovernanceAuthority
    from .import_cycles_tests import TestsFlextInfraImportCycles
    from .init_tests import TestsFlextInfraValidateInit
    from .inventory_tests import TestsFlextInfraInventory
    from .lazy_map_freshness_tests import TestsFlextInfraLazyMapFreshness
    from .loc_delta_tests import TestsFlextInfraLocDelta
    from .main_cli_tests import TestsFlextInfraValidateCli
    from .main_tests import TestsFlextInfraValidateMain
    from .manual_command_tests import TestsFlextInfraManualCommand
    from .metadata_discipline_tests import TestsFlextInfraMetadataDiscipline
    from .namespace_validator_tests import TestsFlextInfraNamespaceValidator
    from .pytest_diag_tests import TestsFlextInfraPytestDiag
    from .scanner_helpers_tests import TestsFlextInfraScannerHelpers
    from .scanner_tests import TestsFlextInfraScanner
    from .silent_failure_tests import TestsFlextInfraSilentFailure
    from .skill_validator_tests import TestsFlextInfraSkillValidator
    from .stub_chain_tests import TestsFlextInfraStubChain
    from .test_core_validation_behavior import TestsCoreValidationBehavior
    from .test_fixture_violations import TestsFixtureViolations
    from .test_import_dag_tests import TestsFlextInfraImportDag
    from .test_module_path_rules import TestsModulePathRules
    from .test_pydantic_legacy_detection import TestsPydanticLegacyDetection
    from .test_rule0_namespace_structure import TestsRule0NamespaceStructure
    from .test_rule1_constants import TestsRule1ConstantsFacade
    from .test_rule2_typings import TestsRule2TypingsFacade
    from .test_rule3_imports import TestsRule3ImportRules
    from .test_rule4_annotations import TestsRule4Annotations
    from .tier_whitelist_tests import TestsFlextInfraTierWhitelist
__all__: tuple[str, ...] = (
    "TestsCoreValidationBehavior",
    "TestsFixtureViolations",
    "TestsFlextInfraFreshImport",
    "TestsFlextInfraGovernanceAuthority",
    "TestsFlextInfraImportCycles",
    "TestsFlextInfraImportDag",
    "TestsFlextInfraInventory",
    "TestsFlextInfraLazyMapFreshness",
    "TestsFlextInfraLocDelta",
    "TestsFlextInfraManualCommand",
    "TestsFlextInfraMetadataDiscipline",
    "TestsFlextInfraNamespaceValidator",
    "TestsFlextInfraPytestDiag",
    "TestsFlextInfraScanner",
    "TestsFlextInfraScannerHelpers",
    "TestsFlextInfraSilentFailure",
    "TestsFlextInfraSkillValidator",
    "TestsFlextInfraStubChain",
    "TestsFlextInfraTierWhitelist",
    "TestsFlextInfraValidateCli",
    "TestsFlextInfraValidateInit",
    "TestsFlextInfraValidateMain",
    "TestsModulePathRules",
    "TestsPydanticLegacyDetection",
    "TestsRule0NamespaceStructure",
    "TestsRule1ConstantsFacade",
    "TestsRule2TypingsFacade",
    "TestsRule3ImportRules",
    "TestsRule4Annotations",
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
            ".fresh_import_tests": ("TestsFlextInfraFreshImport",),
            ".governance_authority_tests": ("TestsFlextInfraGovernanceAuthority",),
            ".import_cycles_tests": ("TestsFlextInfraImportCycles",),
            ".init_tests": ("TestsFlextInfraValidateInit",),
            ".inventory_tests": ("TestsFlextInfraInventory",),
            ".lazy_map_freshness_tests": ("TestsFlextInfraLazyMapFreshness",),
            ".loc_delta_tests": ("TestsFlextInfraLocDelta",),
            ".main_cli_tests": ("TestsFlextInfraValidateCli",),
            ".main_tests": ("TestsFlextInfraValidateMain",),
            ".manual_command_tests": ("TestsFlextInfraManualCommand",),
            ".metadata_discipline_tests": ("TestsFlextInfraMetadataDiscipline",),
            ".namespace_validator_tests": ("TestsFlextInfraNamespaceValidator",),
            ".pytest_diag_tests": ("TestsFlextInfraPytestDiag",),
            ".scanner_helpers_tests": ("TestsFlextInfraScannerHelpers",),
            ".scanner_tests": ("TestsFlextInfraScanner",),
            ".silent_failure_tests": ("TestsFlextInfraSilentFailure",),
            ".skill_validator_tests": ("TestsFlextInfraSkillValidator",),
            ".stub_chain_tests": ("TestsFlextInfraStubChain",),
            ".test_core_validation_behavior": ("TestsCoreValidationBehavior",),
            ".test_fixture_violations": ("TestsFixtureViolations",),
            ".test_import_dag_tests": ("TestsFlextInfraImportDag",),
            ".test_module_path_rules": ("TestsModulePathRules",),
            ".test_pydantic_legacy_detection": ("TestsPydanticLegacyDetection",),
            ".test_rule0_namespace_structure": ("TestsRule0NamespaceStructure",),
            ".test_rule1_constants": ("TestsRule1ConstantsFacade",),
            ".test_rule2_typings": ("TestsRule2TypingsFacade",),
            ".test_rule3_imports": ("TestsRule3ImportRules",),
            ".test_rule4_annotations": ("TestsRule4Annotations",),
            ".tier_whitelist_tests": ("TestsFlextInfraTierWhitelist",),
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
