# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check services for quality gate execution."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.check import cli, services, workspace_check
    from flext_infra.check.cli import FlextInfraCliCheck
    from flext_infra.check.services import (
        FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check import build_parser, main, run_cli

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliCheck": ["flext_infra.check.cli", "FlextInfraCliCheck"],
    "FlextInfraConfigFixer": ["flext_infra.check.services", "FlextInfraConfigFixer"],
    "FlextInfraWorkspaceChecker": [
        "flext_infra.check.services",
        "FlextInfraWorkspaceChecker",
    ],
    "build_parser": ["flext_infra.check.workspace_check", "build_parser"],
    "cli": ["flext_infra.check.cli", ""],
    "main": ["flext_infra.check.workspace_check", "main"],
    "run_cli": ["flext_infra.check.workspace_check", "run_cli"],
    "services": ["flext_infra.check.services", ""],
    "workspace_check": ["flext_infra.check.workspace_check", ""],
}

__all__ = [
    "FlextInfraCliCheck",
    "FlextInfraConfigFixer",
    "FlextInfraWorkspaceChecker",
    "build_parser",
    "cli",
    "main",
    "run_cli",
    "services",
    "workspace_check",
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
