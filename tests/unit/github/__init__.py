# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.github.main_cli_tests import (
        test_main_returns_nonzero_on_unknown,
        test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options,
    )
    from tests.unit.github.main_dispatch_tests import TestRunPrWorkspace
    from tests.unit.github.main_integration_tests import TestMain
    from tests.unit.github.main_tests import TestRunLint, TestRunPr, TestRunWorkflows

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestMain": ["tests.unit.github.main_integration_tests", "TestMain"],
    "TestRunLint": ["tests.unit.github.main_tests", "TestRunLint"],
    "TestRunPr": ["tests.unit.github.main_tests", "TestRunPr"],
    "TestRunPrWorkspace": [
        "tests.unit.github.main_dispatch_tests",
        "TestRunPrWorkspace",
    ],
    "TestRunWorkflows": ["tests.unit.github.main_tests", "TestRunWorkflows"],
    "test_main_returns_nonzero_on_unknown": [
        "tests.unit.github.main_cli_tests",
        "test_main_returns_nonzero_on_unknown",
    ],
    "test_main_returns_zero_on_help": [
        "tests.unit.github.main_cli_tests",
        "test_main_returns_zero_on_help",
    ],
    "test_pr_workspace_accepts_repeated_project_options": [
        "tests.unit.github.main_cli_tests",
        "test_pr_workspace_accepts_repeated_project_options",
    ],
}

__all__ = [
    "TestMain",
    "TestRunLint",
    "TestRunPr",
    "TestRunPrWorkspace",
    "TestRunWorkflows",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_zero_on_help",
    "test_pr_workspace_accepts_repeated_project_options",
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
