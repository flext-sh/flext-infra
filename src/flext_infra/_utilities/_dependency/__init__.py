# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Dependency package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._dependency.deptry import (
        FlextInfraUtilitiesDependencyDeptry,
    )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesDependencyDeptry",)

install_lazy_exports(
    __name__,
    globals(),
    {"FlextInfraUtilitiesDependencyDeptry": ".deptry"},
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesDependencyDeptry": (
            "capture_deptry_scan",
            "_validated_deptry_coverage",
            "_declared_wheel_target",
            "_shipped_import_base",
            "_declared_deptry_roots",
            "_authenticated_deptry_sources",
            "_verified_deptry_sources",
            "_captured_deptry_inputs",
            "_run_deptry",
            "_parsed_deptry_report",
            "_captured_deptry_native",
            "_rechecked_deptry_states",
        ),
    },
)
