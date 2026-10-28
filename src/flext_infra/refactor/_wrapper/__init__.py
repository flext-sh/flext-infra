# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for wrapper.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor._wrapper.rewrite import FlextInfraRefactorWrapperRewrite

__all__: tuple[str, ...] = ("FlextInfraRefactorWrapperRewrite",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRefactorWrapperRewrite": ".rewrite",
    }),
    public_exports=__all__,
)
