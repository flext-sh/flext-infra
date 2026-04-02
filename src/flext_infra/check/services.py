"""FLEXT infrastructure check services.

Re-exports FlextInfraWorkspaceChecker and FlextInfraConfigFixer
for backwards-compatible imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import lazy_getattr
from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import FlextInfraConfigFixer, FlextInfraWorkspaceChecker

_LAZY_IMPORTS: t.StrSequenceMapping = {
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


def __getattr__(name: str) -> type:
    """Lazy-load module attributes on first access (PEP 562)."""
    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    if isinstance(value, type):
        return value
    msg = f"{__name__} export {name!r} did not resolve to a class"
    raise AttributeError(msg)
