# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots,
    )
    from .test_formatting import TestFormattingRunRuffFix
    from .test_iteration import TestIterWorkspacePythonModules
    from .test_parsing import TestParsingModuleAst, TestParsingModuleCst
    from .test_safety import TestSafetyCheckpoint, TestSafetyRollback
    from .test_scanning import TestScanModels

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestDiscoveryDiscoverProjects": (
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryDiscoverProjects",
    ),
    "TestDiscoveryFindAllPyprojectFiles": (
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryFindAllPyprojectFiles",
    ),
    "TestDiscoveryIterPythonFiles": (
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryIterPythonFiles",
    ),
    "TestDiscoveryProjectRoots": (
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryProjectRoots",
    ),
    "TestFormattingRunRuffFix": (
        "tests.unit._utilities.test_formatting",
        "TestFormattingRunRuffFix",
    ),
    "TestIterWorkspacePythonModules": (
        "tests.unit._utilities.test_iteration",
        "TestIterWorkspacePythonModules",
    ),
    "TestParsingModuleAst": (
        "tests.unit._utilities.test_parsing",
        "TestParsingModuleAst",
    ),
    "TestParsingModuleCst": (
        "tests.unit._utilities.test_parsing",
        "TestParsingModuleCst",
    ),
    "TestSafetyCheckpoint": (
        "tests.unit._utilities.test_safety",
        "TestSafetyCheckpoint",
    ),
    "TestSafetyRollback": ("tests.unit._utilities.test_safety", "TestSafetyRollback"),
    "TestScanModels": ("tests.unit._utilities.test_scanning", "TestScanModels"),
}

__all__ = [
    "TestDiscoveryDiscoverProjects",
    "TestDiscoveryFindAllPyprojectFiles",
    "TestDiscoveryIterPythonFiles",
    "TestDiscoveryProjectRoots",
    "TestFormattingRunRuffFix",
    "TestIterWorkspacePythonModules",
    "TestParsingModuleAst",
    "TestParsingModuleCst",
    "TestSafetyCheckpoint",
    "TestSafetyRollback",
    "TestScanModels",
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
