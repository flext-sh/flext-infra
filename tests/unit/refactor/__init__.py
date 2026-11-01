# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.refactor package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.refactor.test_infra_refactor_import_normalization_order import (
        TestsFlextInfraRefactorImportNormalizationOrder,
    )


__all__: tuple[str, ...] = ("TestsFlextInfraRefactorImportNormalizationOrder",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "TestsFlextInfraRefactorImportNormalizationOrder": (
            ".test_infra_refactor_import_normalization_order"
        ),
    }),
    public_exports=__all__,
)
