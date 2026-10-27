# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.test_pytest_markdown_models import (
        TestsFlextInfraPytestMarkdownModels,
    )


__all__: tuple[str, ...] = ("TestsFlextInfraPytestMarkdownModels",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "TestsFlextInfraPytestMarkdownModels": ".test_pytest_markdown_models",
    }),
    public_exports=__all__,
)
