"""Extracted facade class for semantic.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.transformers._semantic import FlextInfraTransformersSemanticPublication


class FlextInfraTransformersSemantic(
    FlextInfraTransformersSemanticPublication,
):
    """Facade for semantic."""


__all__: list[str] = ["FlextInfraTransformersSemantic"]
