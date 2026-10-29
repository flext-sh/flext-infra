# AUTO-GENERATED FILE — Regenerate with: make gen
"""rename package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codemod._rename.sources import FlextInfraCodemodRenameSources
    from flext_infra.codemod._rename.symbols import FlextInfraCodemodRenameSymbols


__all__: tuple[str, ...] = (
    "FlextInfraCodemodRenameSources",
    "FlextInfraCodemodRenameSymbols",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodemodRenameSources": ".sources",
        "FlextInfraCodemodRenameSymbols": ".symbols",
    }),
    public_exports=__all__,
)
