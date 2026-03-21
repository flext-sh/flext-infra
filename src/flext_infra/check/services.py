"""FLEXT infrastructure check services.

Re-exports FlextInfraWorkspaceChecker and FlextInfraConfigFixer
for backwards-compatible imports.
"""

from __future__ import annotations

from flext_core.lazy import lazy_getattr
from flext_infra import FlextInfraConfigFixer, FlextInfraWorkspaceChecker, t

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
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


def __getattr__(name: str) -> t.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
