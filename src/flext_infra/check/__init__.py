# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.check._workspace.check_reports import (
        FlextInfraCheckWorkspaceCheckReports,
    )
    from flext_infra.check.gate_registry import FlextInfraGateRegistry
    from flext_infra.check.workspace import FlextInfraCheckWorkspace
    from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
    from flext_infra.check.workspace_check_gates import (
        FlextInfraWorkspaceCheckGatesMixin,
    )
    from flext_infra.check.workspace_check_union import (
        FlextInfraWorkspaceCheckUnionMixin,
    )


__all__: tuple[str, ...] = (
    "FlextInfraCheckWorkspace",
    "FlextInfraCheckWorkspaceCheckReports",
    "FlextInfraGateRegistry",
    "FlextInfraWorkspaceCheckGatesMixin",
    "FlextInfraWorkspaceCheckUnionMixin",
    "FlextInfraWorkspaceChecker",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCheckWorkspace": ".workspace",
        "FlextInfraCheckWorkspaceCheckReports": "._workspace.check_reports",
        "FlextInfraGateRegistry": ".gate_registry",
        "FlextInfraWorkspaceCheckGatesMixin": ".workspace_check_gates",
        "FlextInfraWorkspaceCheckUnionMixin": ".workspace_check_union",
        "FlextInfraWorkspaceChecker": ".workspace_check",
    }),
    public_exports=__all__,
)
