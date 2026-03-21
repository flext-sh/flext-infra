# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Core package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .basemk_validator_tests import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )
    from .init_tests import TestCoreModuleInit
    from .inventory_tests import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )
    from .main_tests import (
        TestMainBaseMkValidate,
        TestMainCliRouting,
        TestMainInventory,
        TestMainScan,
    )
    from .pytest_diag import (
        TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing,
        TestPytestDiagParseXml,
    )
    from .scanner_tests import TestScannerCore, TestScannerHelpers, TestScannerMultiFile
    from .skill_validator_tests import (
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
        TestStringList,
    )
    from .stub_chain_tests import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestBaseMkValidatorCore": (
        "tests.infra.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorCore",
    ),
    "TestBaseMkValidatorEdgeCases": (
        "tests.infra.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorEdgeCases",
    ),
    "TestBaseMkValidatorSha256": (
        "tests.infra.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorSha256",
    ),
    "TestCoreModuleInit": (
        "tests.infra.unit.validate.init_tests",
        "TestCoreModuleInit",
    ),
    "TestInventoryServiceCore": (
        "tests.infra.unit.validate.inventory_tests",
        "TestInventoryServiceCore",
    ),
    "TestInventoryServiceReports": (
        "tests.infra.unit.validate.inventory_tests",
        "TestInventoryServiceReports",
    ),
    "TestInventoryServiceScripts": (
        "tests.infra.unit.validate.inventory_tests",
        "TestInventoryServiceScripts",
    ),
    "TestMainBaseMkValidate": (
        "tests.infra.unit.validate.main_tests",
        "TestMainBaseMkValidate",
    ),
    "TestMainCliRouting": (
        "tests.infra.unit.validate.main_tests",
        "TestMainCliRouting",
    ),
    "TestMainInventory": ("tests.infra.unit.validate.main_tests", "TestMainInventory"),
    "TestMainScan": ("tests.infra.unit.validate.main_tests", "TestMainScan"),
    "TestPytestDiagExtractorCore": (
        "tests.infra.unit.validate.pytest_diag",
        "TestPytestDiagExtractorCore",
    ),
    "TestPytestDiagLogParsing": (
        "tests.infra.unit.validate.pytest_diag",
        "TestPytestDiagLogParsing",
    ),
    "TestPytestDiagParseXml": (
        "tests.infra.unit.validate.pytest_diag",
        "TestPytestDiagParseXml",
    ),
    "TestSafeLoadYaml": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSafeLoadYaml",
    ),
    "TestScannerCore": ("tests.infra.unit.validate.scanner_tests", "TestScannerCore"),
    "TestScannerHelpers": (
        "tests.infra.unit.validate.scanner_tests",
        "TestScannerHelpers",
    ),
    "TestScannerMultiFile": (
        "tests.infra.unit.validate.scanner_tests",
        "TestScannerMultiFile",
    ),
    "TestSkillValidatorAstGrepCount": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSkillValidatorAstGrepCount",
    ),
    "TestSkillValidatorCore": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSkillValidatorCore",
    ),
    "TestSkillValidatorRenderTemplate": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSkillValidatorRenderTemplate",
    ),
    "TestStringList": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestStringList",
    ),
    "TestStubChainAnalyze": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainAnalyze",
    ),
    "TestStubChainCore": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainCore",
    ),
    "TestStubChainDiscoverProjects": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainDiscoverProjects",
    ),
    "TestStubChainIsInternal": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainIsInternal",
    ),
    "TestStubChainStubExists": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainStubExists",
    ),
    "TestStubChainValidate": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainValidate",
    ),
    "v": ("tests.infra.unit.validate.basemk_validator_tests", "v"),
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
    "v",
]


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
