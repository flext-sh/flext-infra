# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.deps package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.deps.test_diagnostic_path_exceptions import (
        TestsFlextInfraDepsDiagnosticPathExceptions,
    )


__all__: tuple[str, ...] = ("TestsFlextInfraDepsDiagnosticPathExceptions",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "TestsFlextInfraDepsDiagnosticPathExceptions": (
            ".test_diagnostic_path_exceptions"
        ),
    }),
    public_exports=__all__,
)
