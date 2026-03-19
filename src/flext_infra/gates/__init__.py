# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Quality gate implementations for the check library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
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
    "FlextInfraRuffFormatGate": ("flext_infra.gates.ruff_format", "FlextInfraRuffFormatGate"),
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


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
