# AUTO-GENERATED FILE — Regenerate with: make gen
"""project package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._project.classifier_deps import (
        FlextInfraRefactorProjectClassifierDeps,
    )
    from flext_infra._project.classifier_family import (
        FlextInfraRefactorProjectClassifierFamily,
    )


__all__: tuple[str, ...] = (
    "FlextInfraRefactorProjectClassifierDeps",
    "FlextInfraRefactorProjectClassifierFamily",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRefactorProjectClassifierDeps": ".classifier_deps",
        "FlextInfraRefactorProjectClassifierFamily": ".classifier_family",
    }),
    public_exports=__all__,
)
