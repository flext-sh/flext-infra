# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

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
    from flext_infra.check.workspace_check_gates import FlextInfraWorkspaceCheckGates
    from flext_infra.check.workspace_check_union import FlextInfraWorkspaceCheckUnion


__all__: tuple[str, ...] = (
    "FlextInfraCheckWorkspace",
    "FlextInfraCheckWorkspaceCheckReports",
    "FlextInfraGateRegistry",
    "FlextInfraWorkspaceCheckGates",
    "FlextInfraWorkspaceCheckUnion",
    "FlextInfraWorkspaceChecker",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCheckWorkspace": ".workspace",
        "FlextInfraCheckWorkspaceCheckReports": "._workspace.check_reports",
        "FlextInfraGateRegistry": ".gate_registry",
        "FlextInfraWorkspaceCheckGates": ".workspace_check_gates",
        "FlextInfraWorkspaceCheckUnion": ".workspace_check_union",
        "FlextInfraWorkspaceChecker": ".workspace_check",
    }),
    public_exports=__all__,
)
