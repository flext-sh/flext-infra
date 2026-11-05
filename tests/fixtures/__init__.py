# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.fixtures package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.fixtures.imported_model_collision import TestsImportedModelCollision
    from tests.fixtures.imported_model_reference import TestsImportedModelReference
    from tests.fixtures.release_forge import TestsFlextInfraReleaseForgeMemory


__all__: tuple[str, ...] = (
    "TestsFlextInfraReleaseForgeMemory",
    "TestsImportedModelCollision",
    "TestsImportedModelReference",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraReleaseForgeMemory": ".release_forge",
        "TestsImportedModelCollision": ".imported_model_collision",
        "TestsImportedModelReference": ".imported_model_reference",
    },
    public_exports=__all__,
)
