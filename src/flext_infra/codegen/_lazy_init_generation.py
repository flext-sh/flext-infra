"""Lazy-init per-directory generation service — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.codegen import FlextInfraCodegenLazyInitGenerationFilePlanMixin


# Root manifests and initializers are synchronized as one artifact set.
class FlextInfraCodegenLazyInitGenerationMixin(
    FlextInfraCodegenLazyInitGenerationFilePlanMixin,
):
    """Plan ``__init__.py`` artifact sets per package directory."""


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationMixin"]
