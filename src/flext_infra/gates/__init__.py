# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Quality gate implementations for the check library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.go import FlextInfraGoGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "FlextInfraBanditGate": ("flext_infra.gates.bandit", "FlextInfraBanditGate"),
    "FlextInfraGoGate": ("flext_infra.gates.go", "FlextInfraGoGate"),
    "FlextInfraMarkdownGate": ("flext_infra.gates.markdown", "FlextInfraMarkdownGate"),
    "FlextInfraMypyGate": ("flext_infra.gates.mypy", "FlextInfraMypyGate"),
    "FlextInfraPyreflyGate": ("flext_infra.gates.pyrefly", "FlextInfraPyreflyGate"),
    "FlextInfraPyrightGate": ("flext_infra.gates.pyright", "FlextInfraPyrightGate"),
    "FlextInfraRuffFormatGate": (
        "flext_infra.gates.ruff_format",
        "FlextInfraRuffFormatGate",
    ),
    "FlextInfraRuffLintGate": ("flext_infra.gates.ruff_lint", "FlextInfraRuffLintGate"),
}

__all__ = [
    "FlextInfraBanditGate",
    "FlextInfraGoGate",
    "FlextInfraMarkdownGate",
    "FlextInfraMypyGate",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
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
