# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Mypy package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._mypy.profile import FlextInfraUtilitiesMypyProfile
    from flext_infra._utilities._mypy.supervisor import (
        FlextInfraUtilitiesMypySupervisor,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesMypyProfile",
    "FlextInfraUtilitiesMypySupervisor",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesMypyProfile": ".profile",
        "FlextInfraUtilitiesMypySupervisor": ".supervisor",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesMypyProfile": ("run_profiled",),
        "FlextInfraUtilitiesMypySupervisor": (
            "ProcessGroupAbsentError",
            "_signal_group",
            "_usage",
            "_ask_group_exit",
            "_kill_group",
            "_supervised_exit_code",
            "run",
        ),
    },
)
