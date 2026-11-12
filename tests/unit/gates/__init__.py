# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.gates package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.gates.test_wrap_structured_blocks import (
        TestsFlextInfraWrapStructuredBlocks,
        TestsFlextInfraWrapTrailingComment,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraWrapStructuredBlocks",
    "TestsFlextInfraWrapTrailingComment",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraWrapStructuredBlocks": ".test_wrap_structured_blocks",
        "TestsFlextInfraWrapTrailingComment": ".test_wrap_structured_blocks",
    },
    public_exports=__all__,
)
