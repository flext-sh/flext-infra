"""Extracted facade class for accessor.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.refactor._accessor import (
    FlextInfraRefactorAccessorOrigin,
    FlextInfraRefactorAccessorReport,
)


class FlextInfraRefactorAccessor(
    FlextInfraRefactorAccessorOrigin,
    FlextInfraRefactorAccessorReport,
):
    """Facade for accessor."""


__all__: list[str] = ["FlextInfraRefactorAccessor"]
