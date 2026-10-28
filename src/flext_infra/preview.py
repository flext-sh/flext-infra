"""Extracted facade class for preview.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._preview import FlextInfraPreviewWiring


class FlextInfraFlextInfraPreview(
    FlextInfraPreviewWiring,
):
    """Facade for preview."""


__all__: list[str] = ["FlextInfraFlextInfraPreview"]
