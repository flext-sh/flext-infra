# AUTO-GENERATED FILE — Regenerate with: make gen
"""fixer package.

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
    from flext_infra._fixer.passes import FlextInfraCodegenFixerPasses
    from flext_infra._fixer.results import FlextInfraCodegenFixerResults
    from flext_infra._fixer.workspace import FlextInfraCodegenFixerWorkspace


__all__: tuple[str, ...] = (
    "FlextInfraCodegenFixerPasses",
    "FlextInfraCodegenFixerResults",
    "FlextInfraCodegenFixerWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegenFixerPasses": ".passes",
        "FlextInfraCodegenFixerResults": ".results",
        "FlextInfraCodegenFixerWorkspace": ".workspace",
    }),
    public_exports=__all__,
)
