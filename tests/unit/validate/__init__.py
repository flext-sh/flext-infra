# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Core package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.validate import (
        basemk_validator_tests as basemk_validator_tests,
        init_tests as init_tests,
        inventory_tests as inventory_tests,
        main_cli_tests as main_cli_tests,
        main_tests as main_tests,
        pytest_diag as pytest_diag,
        scanner_tests as scanner_tests,
        skill_validator_tests as skill_validator_tests,
        stub_chain_tests as stub_chain_tests,
    )
    from tests.unit.validate.basemk_validator_tests import (
        TestBaseMkValidatorCore as TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases as TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256 as TestBaseMkValidatorSha256,
        v as v,
    )
    from tests.unit.validate.init_tests import TestCoreModuleInit as TestCoreModuleInit
    from tests.unit.validate.inventory_tests import (
        TestInventoryServiceCore as TestInventoryServiceCore,
        TestInventoryServiceReports as TestInventoryServiceReports,
        TestInventoryServiceScripts as TestInventoryServiceScripts,
    )
    from tests.unit.validate.main_cli_tests import (
        test_stub_validate_help_returns_zero as test_stub_validate_help_returns_zero,
        test_stub_validate_uses_all_flag as test_stub_validate_uses_all_flag,
    )
    from tests.unit.validate.main_tests import (
        TestMainBaseMkValidate as TestMainBaseMkValidate,
        TestMainCliRouting as TestMainCliRouting,
        TestMainInventory as TestMainInventory,
        TestMainScan as TestMainScan,
    )
    from tests.unit.validate.pytest_diag import (
        TestPytestDiagExtractorCore as TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing as TestPytestDiagLogParsing,
        TestPytestDiagParseXml as TestPytestDiagParseXml,
    )
    from tests.unit.validate.scanner_tests import (
        TestScannerCore as TestScannerCore,
        TestScannerHelpers as TestScannerHelpers,
        TestScannerMultiFile as TestScannerMultiFile,
    )
    from tests.unit.validate.skill_validator_tests import (
        TestSafeLoadYaml as TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount as TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore as TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate as TestSkillValidatorRenderTemplate,
        TestStringList as TestStringList,
    )
    from tests.unit.validate.stub_chain_tests import (
        TestStubChainAnalyze as TestStubChainAnalyze,
        TestStubChainCore as TestStubChainCore,
        TestStubChainDiscoverProjects as TestStubChainDiscoverProjects,
        TestStubChainIsInternal as TestStubChainIsInternal,
        TestStubChainStubExists as TestStubChainStubExists,
        TestStubChainValidate as TestStubChainValidate,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestBaseMkValidatorCore": [
        "tests.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorCore",
    ],
    "TestBaseMkValidatorEdgeCases": [
        "tests.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorEdgeCases",
    ],
    "TestBaseMkValidatorSha256": [
        "tests.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorSha256",
    ],
    "TestCoreModuleInit": ["tests.unit.validate.init_tests", "TestCoreModuleInit"],
    "TestInventoryServiceCore": [
        "tests.unit.validate.inventory_tests",
        "TestInventoryServiceCore",
    ],
    "TestInventoryServiceReports": [
        "tests.unit.validate.inventory_tests",
        "TestInventoryServiceReports",
    ],
    "TestInventoryServiceScripts": [
        "tests.unit.validate.inventory_tests",
        "TestInventoryServiceScripts",
    ],
    "TestMainBaseMkValidate": [
        "tests.unit.validate.main_tests",
        "TestMainBaseMkValidate",
    ],
    "TestMainCliRouting": ["tests.unit.validate.main_tests", "TestMainCliRouting"],
    "TestMainInventory": ["tests.unit.validate.main_tests", "TestMainInventory"],
    "TestMainScan": ["tests.unit.validate.main_tests", "TestMainScan"],
    "TestPytestDiagExtractorCore": [
        "tests.unit.validate.pytest_diag",
        "TestPytestDiagExtractorCore",
    ],
    "TestPytestDiagLogParsing": [
        "tests.unit.validate.pytest_diag",
        "TestPytestDiagLogParsing",
    ],
    "TestPytestDiagParseXml": [
        "tests.unit.validate.pytest_diag",
        "TestPytestDiagParseXml",
    ],
    "TestSafeLoadYaml": [
        "tests.unit.validate.skill_validator_tests",
        "TestSafeLoadYaml",
    ],
    "TestScannerCore": ["tests.unit.validate.scanner_tests", "TestScannerCore"],
    "TestScannerHelpers": ["tests.unit.validate.scanner_tests", "TestScannerHelpers"],
    "TestScannerMultiFile": [
        "tests.unit.validate.scanner_tests",
        "TestScannerMultiFile",
    ],
    "TestSkillValidatorAstGrepCount": [
        "tests.unit.validate.skill_validator_tests",
        "TestSkillValidatorAstGrepCount",
    ],
    "TestSkillValidatorCore": [
        "tests.unit.validate.skill_validator_tests",
        "TestSkillValidatorCore",
    ],
    "TestSkillValidatorRenderTemplate": [
        "tests.unit.validate.skill_validator_tests",
        "TestSkillValidatorRenderTemplate",
    ],
    "TestStringList": ["tests.unit.validate.skill_validator_tests", "TestStringList"],
    "TestStubChainAnalyze": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainAnalyze",
    ],
    "TestStubChainCore": ["tests.unit.validate.stub_chain_tests", "TestStubChainCore"],
    "TestStubChainDiscoverProjects": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainDiscoverProjects",
    ],
    "TestStubChainIsInternal": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainIsInternal",
    ],
    "TestStubChainStubExists": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainStubExists",
    ],
    "TestStubChainValidate": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainValidate",
    ],
    "basemk_validator_tests": ["tests.unit.validate.basemk_validator_tests", ""],
    "init_tests": ["tests.unit.validate.init_tests", ""],
    "inventory_tests": ["tests.unit.validate.inventory_tests", ""],
    "main_cli_tests": ["tests.unit.validate.main_cli_tests", ""],
    "main_tests": ["tests.unit.validate.main_tests", ""],
    "pytest_diag": ["tests.unit.validate.pytest_diag", ""],
    "scanner_tests": ["tests.unit.validate.scanner_tests", ""],
    "skill_validator_tests": ["tests.unit.validate.skill_validator_tests", ""],
    "stub_chain_tests": ["tests.unit.validate.stub_chain_tests", ""],
    "test_stub_validate_help_returns_zero": [
        "tests.unit.validate.main_cli_tests",
        "test_stub_validate_help_returns_zero",
    ],
    "test_stub_validate_uses_all_flag": [
        "tests.unit.validate.main_cli_tests",
        "test_stub_validate_uses_all_flag",
    ],
    "v": ["tests.unit.validate.basemk_validator_tests", "v"],
}

_EXPORTS: Sequence[str] = [
    "TestBaseMkValidatorCore",
    "TestBaseMkValidatorEdgeCases",
    "TestBaseMkValidatorSha256",
    "TestCoreModuleInit",
    "TestInventoryServiceCore",
    "TestInventoryServiceReports",
    "TestInventoryServiceScripts",
    "TestMainBaseMkValidate",
    "TestMainCliRouting",
    "TestMainInventory",
    "TestMainScan",
    "TestPytestDiagExtractorCore",
    "TestPytestDiagLogParsing",
    "TestPytestDiagParseXml",
    "TestSafeLoadYaml",
    "TestScannerCore",
    "TestScannerHelpers",
    "TestScannerMultiFile",
    "TestSkillValidatorAstGrepCount",
    "TestSkillValidatorCore",
    "TestSkillValidatorRenderTemplate",
    "TestStringList",
    "TestStubChainAnalyze",
    "TestStubChainCore",
    "TestStubChainDiscoverProjects",
    "TestStubChainIsInternal",
    "TestStubChainStubExists",
    "TestStubChainValidate",
    "basemk_validator_tests",
    "init_tests",
    "inventory_tests",
    "main_cli_tests",
    "main_tests",
    "pytest_diag",
    "scanner_tests",
    "skill_validator_tests",
    "stub_chain_tests",
    "test_stub_validate_help_returns_zero",
    "test_stub_validate_uses_all_flag",
    "v",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
