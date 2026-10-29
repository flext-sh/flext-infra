# AUTO-GENERATED FILE — Regenerate with: make gen
"""codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._codegen.vscode import FlextInfraCodegenVscode


__all__: tuple[str, ...] = ("FlextInfraCodegenVscode",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegenVscode": ".vscode",
    }),
    public_exports=__all__,
)
