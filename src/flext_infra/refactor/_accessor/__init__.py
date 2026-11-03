# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.refactor. Accessor package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor._accessor.expression import (
        FlextInfraRefactorAccessorExpression,
    )
    from flext_infra.refactor._accessor.origin import FlextInfraRefactorAccessorOrigin
    from flext_infra.refactor._accessor.report import FlextInfraRefactorAccessorReport
    from flext_infra.refactor._accessor.rewrite import FlextInfraRefactorAccessorRewrite
    from flext_infra.refactor._accessor.warnings import (
        FlextInfraRefactorAccessorWarnings,
    )


__all__: tuple[str, ...] = (
    "FlextInfraRefactorAccessorExpression",
    "FlextInfraRefactorAccessorOrigin",
    "FlextInfraRefactorAccessorReport",
    "FlextInfraRefactorAccessorRewrite",
    "FlextInfraRefactorAccessorWarnings",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraRefactorAccessorExpression": ".expression",
        "FlextInfraRefactorAccessorOrigin": ".origin",
        "FlextInfraRefactorAccessorReport": ".report",
        "FlextInfraRefactorAccessorRewrite": ".rewrite",
        "FlextInfraRefactorAccessorWarnings": ".warnings",
    },
    public_exports=__all__,
)
