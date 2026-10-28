# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codemod._loop.phase_accessor_rename import (
        FlextInfraCodemodLoopPhaseAccessorRename,
    )
    from flext_infra.codemod._loop.phase_duplicate_apply import (
        FlextInfraCodemodLoopPhaseDuplicateApply,
    )
    from flext_infra.codemod._loop.phase_import_normalization import (
        FlextInfraCodemodLoopPhaseImportNormalization,
    )
    from flext_infra.codemod._loop.phase_namespace_relocation import (
        FlextInfraCodemodLoopPhaseNamespaceRelocation,
    )

__all__: tuple[str, ...] = (
    "FlextInfraCodemodLoopPhaseAccessorRename",
    "FlextInfraCodemodLoopPhaseDuplicateApply",
    "FlextInfraCodemodLoopPhaseImportNormalization",
    "FlextInfraCodemodLoopPhaseNamespaceRelocation",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodemodLoopPhaseAccessorRename": ".phase_accessor_rename",
        "FlextInfraCodemodLoopPhaseDuplicateApply": ".phase_duplicate_apply",
        "FlextInfraCodemodLoopPhaseImportNormalization": ".phase_import_normalization",
        "FlextInfraCodemodLoopPhaseNamespaceRelocation": ".phase_namespace_relocation",
    }),
    public_exports=__all__,
)
