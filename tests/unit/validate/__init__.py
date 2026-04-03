# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Validate package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.validate.basemk_validator_tests as _tests_unit_validate_basemk_validator_tests

    basemk_validator_tests = _tests_unit_validate_basemk_validator_tests
    import tests.unit.validate.init_tests as _tests_unit_validate_init_tests
    from tests.unit.validate.basemk_validator_tests import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )

    init_tests = _tests_unit_validate_init_tests
    import tests.unit.validate.inventory_tests as _tests_unit_validate_inventory_tests
    from tests.unit.validate.init_tests import TestCoreModuleInit

    inventory_tests = _tests_unit_validate_inventory_tests
    import tests.unit.validate.main_cli_tests as _tests_unit_validate_main_cli_tests
    from tests.unit.validate.inventory_tests import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )

    main_cli_tests = _tests_unit_validate_main_cli_tests
    import tests.unit.validate.main_tests as _tests_unit_validate_main_tests
    from tests.unit.validate.main_cli_tests import (
        test_stub_validate_help_returns_zero,
        test_stub_validate_uses_all_flag,
    )

    main_tests = _tests_unit_validate_main_tests
    import tests.unit.validate.pytest_diag as _tests_unit_validate_pytest_diag
    from tests.unit.validate.main_tests import (
        TestMainBaseMkValidate,
        TestMainCliRouting,
        TestMainInventory,
        TestMainScan,
    )

    pytest_diag = _tests_unit_validate_pytest_diag
    import tests.unit.validate.scanner_tests as _tests_unit_validate_scanner_tests
    from tests.unit.validate.pytest_diag import (
        TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing,
        TestPytestDiagParseXml,
    )

    scanner_tests = _tests_unit_validate_scanner_tests
    import tests.unit.validate.skill_validator_tests as _tests_unit_validate_skill_validator_tests
    from tests.unit.validate.scanner_tests import (
        TestScannerCore,
        TestScannerHelpers,
        TestScannerMultiFile,
    )

    skill_validator_tests = _tests_unit_validate_skill_validator_tests
    import tests.unit.validate.stub_chain_tests as _tests_unit_validate_stub_chain_tests
    from tests.unit.validate.skill_validator_tests import (
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
        TestStringList,
    )

    stub_chain_tests = _tests_unit_validate_stub_chain_tests
    from tests.unit.validate.stub_chain_tests import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )

    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
_LAZY_IMPORTS = {
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
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.validate.init_tests",
    "inventory_tests": "tests.unit.validate.inventory_tests",
    "m": ("flext_core.models", "FlextModels"),
    "main_cli_tests": "tests.unit.validate.main_cli_tests",
    "main_tests": "tests.unit.validate.main_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pytest_diag": "tests.unit.validate.pytest_diag",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scanner_tests": "tests.unit.validate.scanner_tests",
    "skill_validator_tests": "tests.unit.validate.skill_validator_tests",
    "stub_chain_tests": "tests.unit.validate.stub_chain_tests",
    "t": ("flext_core.typings", "FlextTypes"),
    "test_stub_validate_help_returns_zero": "tests.unit.validate.main_cli_tests",
    "test_stub_validate_uses_all_flag": "tests.unit.validate.main_cli_tests",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "v": "tests.unit.validate.basemk_validator_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
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
    "c",
    "d",
    "e",
    "h",
    "init_tests",
    "inventory_tests",
    "m",
    "main_cli_tests",
    "main_tests",
    "p",
    "pytest_diag",
    "r",
    "s",
    "scanner_tests",
    "skill_validator_tests",
    "stub_chain_tests",
    "t",
    "test_stub_validate_help_returns_zero",
    "test_stub_validate_uses_all_flag",
    "u",
    "v",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
