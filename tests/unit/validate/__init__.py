# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Core package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from tests.unit.validate import (
        basemk_validator_tests,
        init_tests,
        inventory_tests,
        main_cli_tests,
        main_tests,
        pytest_diag,
        scanner_tests,
        skill_validator_tests,
        stub_chain_tests,
    )
    from tests.unit.validate.basemk_validator_tests import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )
    from tests.unit.validate.init_tests import TestCoreModuleInit
    from tests.unit.validate.inventory_tests import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )
    from tests.unit.validate.main_cli_tests import (
        test_stub_validate_help_returns_zero,
        test_stub_validate_uses_all_flag,
    )
    from tests.unit.validate.main_tests import (
        TestMainBaseMkValidate,
        TestMainCliRouting,
        TestMainInventory,
        TestMainScan,
    )
    from tests.unit.validate.pytest_diag import (
        TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing,
        TestPytestDiagParseXml,
    )
    from tests.unit.validate.scanner_tests import (
        TestScannerCore,
        TestScannerHelpers,
        TestScannerMultiFile,
    )
    from tests.unit.validate.skill_validator_tests import (
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
        TestStringList,
    )
    from tests.unit.validate.stub_chain_tests import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "TestBaseMkValidatorCore": "tests.unit.validate.basemk_validator_tests",
    "TestBaseMkValidatorEdgeCases": "tests.unit.validate.basemk_validator_tests",
    "TestBaseMkValidatorSha256": "tests.unit.validate.basemk_validator_tests",
    "TestCoreModuleInit": "tests.unit.validate.init_tests",
    "TestInventoryServiceCore": "tests.unit.validate.inventory_tests",
    "TestInventoryServiceReports": "tests.unit.validate.inventory_tests",
    "TestInventoryServiceScripts": "tests.unit.validate.inventory_tests",
    "TestMainBaseMkValidate": "tests.unit.validate.main_tests",
    "TestMainCliRouting": "tests.unit.validate.main_tests",
    "TestMainInventory": "tests.unit.validate.main_tests",
    "TestMainScan": "tests.unit.validate.main_tests",
    "TestPytestDiagExtractorCore": "tests.unit.validate.pytest_diag",
    "TestPytestDiagLogParsing": "tests.unit.validate.pytest_diag",
    "TestPytestDiagParseXml": "tests.unit.validate.pytest_diag",
    "TestSafeLoadYaml": "tests.unit.validate.skill_validator_tests",
    "TestScannerCore": "tests.unit.validate.scanner_tests",
    "TestScannerHelpers": "tests.unit.validate.scanner_tests",
    "TestScannerMultiFile": "tests.unit.validate.scanner_tests",
    "TestSkillValidatorAstGrepCount": "tests.unit.validate.skill_validator_tests",
    "TestSkillValidatorCore": "tests.unit.validate.skill_validator_tests",
    "TestSkillValidatorRenderTemplate": "tests.unit.validate.skill_validator_tests",
    "TestStringList": "tests.unit.validate.skill_validator_tests",
    "TestStubChainAnalyze": "tests.unit.validate.stub_chain_tests",
    "TestStubChainCore": "tests.unit.validate.stub_chain_tests",
    "TestStubChainDiscoverProjects": "tests.unit.validate.stub_chain_tests",
    "TestStubChainIsInternal": "tests.unit.validate.stub_chain_tests",
    "TestStubChainStubExists": "tests.unit.validate.stub_chain_tests",
    "TestStubChainValidate": "tests.unit.validate.stub_chain_tests",
    "basemk_validator_tests": "tests.unit.validate.basemk_validator_tests",
    "init_tests": "tests.unit.validate.init_tests",
    "inventory_tests": "tests.unit.validate.inventory_tests",
    "main_cli_tests": "tests.unit.validate.main_cli_tests",
    "main_tests": "tests.unit.validate.main_tests",
    "pytest_diag": "tests.unit.validate.pytest_diag",
    "scanner_tests": "tests.unit.validate.scanner_tests",
    "skill_validator_tests": "tests.unit.validate.skill_validator_tests",
    "stub_chain_tests": "tests.unit.validate.stub_chain_tests",
    "test_stub_validate_help_returns_zero": "tests.unit.validate.main_cli_tests",
    "test_stub_validate_uses_all_flag": "tests.unit.validate.main_cli_tests",
    "v": "tests.unit.validate.basemk_validator_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
