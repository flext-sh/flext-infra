# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker as FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check_gates import (
        FlextInfraGateRegistry as FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin as FlextInfraWorkspaceCheckGatesMixin,
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
