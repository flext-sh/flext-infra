# AUTO-GENERATED FILE — Regenerate with: make gen
"""preview package.

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
    from flext_infra._preview.wiring import FlextInfraPreviewWiring


__all__: tuple[str, ...] = ("FlextInfraPreviewWiring",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraPreviewWiring": ".wiring",
    }),
    public_exports=__all__,
)
