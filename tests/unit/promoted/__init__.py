# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.promoted package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.promoted.test_command_header import (
        TestsFlextInfraPromotedCommandHeader,
    )


__all__: tuple[str, ...] = ("TestsFlextInfraPromotedCommandHeader",)

install_lazy_exports(
    __name__,
    globals(),
    {"TestsFlextInfraPromotedCommandHeader": ".test_command_header"},
    public_exports=__all__,
)
