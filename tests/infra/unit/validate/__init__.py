# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Core package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .basemk_validator import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )
    from .init import TestCoreModuleInit
    from .inventory import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )
    from .main import (
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
    from .scanner import TestScannerCore, TestScannerHelpers, TestScannerMultiFile
    from .skill_validator import (
        TestNormalizeStringList,
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
    )
    from .stub_chain import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestBaseMkValidatorCore": (
        "tests.infra.unit.validate.basemk_validator",
        "TestBaseMkValidatorCore",
    ),
    "TestBaseMkValidatorEdgeCases": (
        "tests.infra.unit.validate.basemk_validator",
        "TestBaseMkValidatorEdgeCases",
    ),
    "TestBaseMkValidatorSha256": (
        "tests.infra.unit.validate.basemk_validator",
        "TestBaseMkValidatorSha256",
    ),
    "TestCoreModuleInit": ("tests.infra.unit.validate.init", "TestCoreModuleInit"),
    "TestInventoryServiceCore": (
        "tests.infra.unit.validate.inventory",
        "TestInventoryServiceCore",
    ),
    "TestInventoryServiceReports": (
        "tests.infra.unit.validate.inventory",
        "TestInventoryServiceReports",
    ),
    "TestInventoryServiceScripts": (
        "tests.infra.unit.validate.inventory",
        "TestInventoryServiceScripts",
    ),
    "TestMainBaseMkValidate": (
        "tests.infra.unit.validate.main",
        "TestMainBaseMkValidate",
    ),
    "TestMainCliRouting": ("tests.infra.unit.validate.main", "TestMainCliRouting"),
    "TestMainInventory": ("tests.infra.unit.validate.main", "TestMainInventory"),
    "TestMainScan": ("tests.infra.unit.validate.main", "TestMainScan"),
    "TestNormalizeStringList": (
        "tests.infra.unit.validate.skill_validator",
        "TestNormalizeStringList",
    ),
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
        "tests.infra.unit.validate.skill_validator",
        "TestSafeLoadYaml",
    ),
    "TestScannerCore": ("tests.infra.unit.validate.scanner", "TestScannerCore"),
    "TestScannerHelpers": ("tests.infra.unit.validate.scanner", "TestScannerHelpers"),
    "TestScannerMultiFile": (
        "tests.infra.unit.validate.scanner",
        "TestScannerMultiFile",
    ),
    "TestSkillValidatorAstGrepCount": (
        "tests.infra.unit.validate.skill_validator",
        "TestSkillValidatorAstGrepCount",
    ),
    "TestSkillValidatorCore": (
        "tests.infra.unit.validate.skill_validator",
        "TestSkillValidatorCore",
    ),
    "TestSkillValidatorRenderTemplate": (
        "tests.infra.unit.validate.skill_validator",
        "TestSkillValidatorRenderTemplate",
    ),
    "TestStubChainAnalyze": (
        "tests.infra.unit.validate.stub_chain",
        "TestStubChainAnalyze",
    ),
    "TestStubChainCore": ("tests.infra.unit.validate.stub_chain", "TestStubChainCore"),
    "TestStubChainDiscoverProjects": (
        "tests.infra.unit.validate.stub_chain",
        "TestStubChainDiscoverProjects",
    ),
    "TestStubChainIsInternal": (
        "tests.infra.unit.validate.stub_chain",
        "TestStubChainIsInternal",
    ),
    "TestStubChainStubExists": (
        "tests.infra.unit.validate.stub_chain",
        "TestStubChainStubExists",
    ),
    "TestStubChainValidate": (
        "tests.infra.unit.validate.stub_chain",
        "TestStubChainValidate",
    ),
    "v": ("tests.infra.unit.validate.basemk_validator", "v"),
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
    "TestNormalizeStringList",
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
    "TestStubChainAnalyze",
    "TestStubChainCore",
    "TestStubChainDiscoverProjects",
    "TestStubChainIsInternal",
    "TestStubChainStubExists",
    "TestStubChainValidate",
    "v",
]


_LAZY_CACHE: dict[str, object] = {}


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
