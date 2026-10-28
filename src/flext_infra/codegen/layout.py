"""Extracted facade class for layout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.codegen._layout import (
    FlextInfraCodegenLayoutApply,
    FlextInfraCodegenLayoutPlan,
)


class FlextInfraCodegenLayout(
    FlextInfraCodegenLayoutApply,
    FlextInfraCodegenLayoutPlan,
):
    """Facade for layout."""


__all__: list[str] = ["FlextInfraCodegenLayout"]
