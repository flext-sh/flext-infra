"""FLEXT infrastructure check services.

Re-exports FlextInfraWorkspaceChecker and FlextInfraConfigFixer
for backwards-compatible imports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra import FlextInfraConfigFixer, FlextInfraWorkspaceChecker

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraWorkspaceChecker": (
        "flext_infra.check.workspace_check",
        "FlextInfraWorkspaceChecker",
    ),
    "FlextInfraConfigFixer": (
        "flext_infra.deps.fix_pyrefly_config",
        "FlextInfraConfigFixer",
    ),
}

__all__ = [
    "FlextInfraConfigFixer",
    "FlextInfraWorkspaceChecker",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
