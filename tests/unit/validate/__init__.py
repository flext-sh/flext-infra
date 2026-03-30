# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Core package."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

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
    "test_stub_validate_help_returns_zero",
    "test_stub_validate_uses_all_flag",
    "v",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
