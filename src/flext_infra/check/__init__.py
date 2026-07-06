# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
    from flext_infra.check.workspace_check_gates import (
        FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".workspace_check": ("FlextInfraWorkspaceChecker",),
        ".workspace_check_gates": (
            "FlextInfraGateRegistry",
            "FlextInfraWorkspaceCheckGatesMixin",
        ),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
