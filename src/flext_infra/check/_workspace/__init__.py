# AUTO-GENERATED FILE — Regenerate with: make gen
"""workspace package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._workspace.check_reports import (
        FlextInfraCheckWorkspaceCheckReports,
    )


__all__: tuple[str, ...] = ("FlextInfraCheckWorkspaceCheckReports",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCheckWorkspaceCheckReports": ".check_reports",
    }),
    public_exports=__all__,
)
