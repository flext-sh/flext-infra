# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Github package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .main_dispatch_tests import TestRunPrWorkspace
    from .main_integration_tests import TestMain
    from .main_tests import (
        SyncOperation,
        TestRunLint,
        TestRunPr,
        TestRunWorkflows,
        main,
        run_lint,
        run_pr,
        run_pr_workspace,
        run_workflows,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "SyncOperation": ("tests.unit.github.main_tests", "SyncOperation"),
    "TestMain": ("tests.unit.github.main_integration_tests", "TestMain"),
    "TestRunLint": ("tests.unit.github.main_tests", "TestRunLint"),
    "TestRunPr": ("tests.unit.github.main_tests", "TestRunPr"),
    "TestRunPrWorkspace": (
        "tests.unit.github.main_dispatch_tests",
        "TestRunPrWorkspace",
    ),
    "TestRunWorkflows": ("tests.unit.github.main_tests", "TestRunWorkflows"),
    "main": ("tests.unit.github.main_tests", "main"),
    "run_lint": ("tests.unit.github.main_tests", "run_lint"),
    "run_pr": ("tests.unit.github.main_tests", "run_pr"),
    "run_pr_workspace": ("tests.unit.github.main_tests", "run_pr_workspace"),
    "run_workflows": ("tests.unit.github.main_tests", "run_workflows"),
}

__all__ = [
    "SyncOperation",
    "TestMain",
    "TestRunLint",
    "TestRunPr",
    "TestRunPrWorkspace",
    "TestRunWorkflows",
    "main",
    "run_lint",
    "run_pr",
    "run_pr_workspace",
    "run_workflows",
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
