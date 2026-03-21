# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Io package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .test_infra_json_io import SampleModel, TestFlextInfraJsonService
    from .test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases,
        TestInfraOutputNoColor,
        TestMroFacadeMethods,
    )
    from .test_infra_output_formatting import (
        ANSI_RE,
        TestInfraOutputHeader,
        TestInfraOutputMessages,
        TestInfraOutputProgress,
        TestInfraOutputStatus,
        TestInfraOutputSummary,
    )
    from .test_infra_terminal_detection import TestShouldUseColor, TestShouldUseUnicode

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ANSI_RE": ("tests.unit.io.test_infra_output_formatting", "ANSI_RE"),
    "SampleModel": ("tests.unit.io.test_infra_json_io", "SampleModel"),
    "TestFlextInfraJsonService": (
        "tests.unit.io.test_infra_json_io",
        "TestFlextInfraJsonService",
    ),
    "TestInfraOutputEdgeCases": (
        "tests.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputEdgeCases",
    ),
    "TestInfraOutputHeader": (
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputHeader",
    ),
    "TestInfraOutputMessages": (
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputMessages",
    ),
    "TestInfraOutputNoColor": (
        "tests.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputNoColor",
    ),
    "TestInfraOutputProgress": (
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputProgress",
    ),
    "TestInfraOutputStatus": (
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputStatus",
    ),
    "TestInfraOutputSummary": (
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputSummary",
    ),
    "TestMroFacadeMethods": (
        "tests.unit.io.test_infra_output_edge_cases",
        "TestMroFacadeMethods",
    ),
    "TestShouldUseColor": (
        "tests.unit.io.test_infra_terminal_detection",
        "TestShouldUseColor",
    ),
    "TestShouldUseUnicode": (
        "tests.unit.io.test_infra_terminal_detection",
        "TestShouldUseUnicode",
    ),
}

__all__ = [
    "ANSI_RE",
    "SampleModel",
    "TestFlextInfraJsonService",
    "TestInfraOutputEdgeCases",
    "TestInfraOutputHeader",
    "TestInfraOutputMessages",
    "TestInfraOutputNoColor",
    "TestInfraOutputProgress",
    "TestInfraOutputStatus",
    "TestInfraOutputSummary",
    "TestMroFacadeMethods",
    "TestShouldUseColor",
    "TestShouldUseUnicode",
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
