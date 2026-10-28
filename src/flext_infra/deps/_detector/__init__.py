# AUTO-GENERATED FILE — Regenerate with: make gen
"""detector package.

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
    from flext_infra._detector.runtime_steps import FlextInfraDepsDetectorRuntimeSteps


__all__: tuple[str, ...] = ("FlextInfraDepsDetectorRuntimeSteps",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraDepsDetectorRuntimeSteps": ".runtime_steps",
    }),
    public_exports=__all__,
)
