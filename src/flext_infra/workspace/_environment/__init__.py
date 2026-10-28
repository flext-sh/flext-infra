# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for environment.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.workspace._environment.provenance_editable import (
        FlextInfraWorkspaceEnvironmentProvenanceEditable,
    )
    from flext_infra.workspace._environment.provenance_module_source import (
        FlextInfraWorkspaceEnvironmentProvenanceModuleSource,
    )

__all__: tuple[str, ...] = (
    "FlextInfraWorkspaceEnvironmentProvenanceEditable",
    "FlextInfraWorkspaceEnvironmentProvenanceModuleSource",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraWorkspaceEnvironmentProvenanceEditable": ".provenance_editable",
        "FlextInfraWorkspaceEnvironmentProvenanceModuleSource": ".provenance_module_source",
    }),
    public_exports=__all__,
)
