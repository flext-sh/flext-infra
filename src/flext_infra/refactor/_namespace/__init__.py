# AUTO-GENERATED FILE — Regenerate with: make gen
"""namespace package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor._namespace.enforcer_project import (
        FlextInfraRefactorNamespaceEnforcerProject,
    )


__all__: tuple[str, ...] = ("FlextInfraRefactorNamespaceEnforcerProject",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRefactorNamespaceEnforcerProject": ".enforcer_project",
    }),
    public_exports=__all__,
)
