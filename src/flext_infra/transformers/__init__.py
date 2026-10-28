# AUTO-GENERATED FILE — Regenerate with: make gen
"""Transformers package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.transformers._semantic.publication import (
        FlextInfraTransformersSemanticPublication,
    )
    from flext_infra.transformers.rope_transformer import FlextInfraRopeTransformer
    from flext_infra.transformers.semantic import FlextInfraTransformersSemantic


__all__: tuple[str, ...] = (
    "FlextInfraRopeTransformer",
    "FlextInfraTransformersSemantic",
    "FlextInfraTransformersSemanticPublication",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRopeTransformer": ".rope_transformer",
        "FlextInfraTransformersSemantic": ".semantic",
        "FlextInfraTransformersSemanticPublication": "._semantic.publication",
    }),
    public_exports=__all__,
)
