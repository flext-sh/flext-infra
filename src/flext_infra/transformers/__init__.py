# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.transformers package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.transformers.rope_transformer import FlextInfraRopeTransformer
    from flext_infra.transformers.semantic import FlextInfraTransformersSemantic


__all__: tuple[str, ...] = (
    "FlextInfraRopeTransformer",
    "FlextInfraTransformersSemantic",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraRopeTransformer": ".rope_transformer",
        "FlextInfraTransformersSemantic": ".semantic",
    },
    public_exports=__all__,
)
