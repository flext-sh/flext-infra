# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Check services for quality gate execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.check.services import (
        CheckIssue,
        FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker,
        GateExecution,
        ProjectResult,
    )
    from flext_infra.check.workspace_check import build_parser, main, run_cli

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "CheckIssue": ("flext_infra.check.services", "CheckIssue"),
    "FlextInfraConfigFixer": ("flext_infra.check.services", "FlextInfraConfigFixer"),
    "FlextInfraWorkspaceChecker": (
        "flext_infra.check.services",
        "FlextInfraWorkspaceChecker",
    ),
    "GateExecution": ("flext_infra.check.services", "GateExecution"),
    "ProjectResult": ("flext_infra.check.services", "ProjectResult"),
    "build_parser": ("flext_infra.check.workspace_check", "build_parser"),
    "main": ("flext_infra.check.workspace_check", "main"),
    "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
}

__all__ = [
    "CheckIssue",
    "FlextInfraConfigFixer",
    "FlextInfraWorkspaceChecker",
    "GateExecution",
    "ProjectResult",
    "build_parser",
    "main",
    "run_cli",
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
