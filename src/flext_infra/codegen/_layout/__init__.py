# AUTO-GENERATED FILE — Regenerate with: make gen
"""layout package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen._layout.apply import FlextInfraCodegenLayoutApply
    from flext_infra.codegen._layout.files import FlextInfraCodegenLayoutFiles
    from flext_infra.codegen._layout.ignore import FlextInfraCodegenLayoutGitignore
    from flext_infra.codegen._layout.plan import FlextInfraCodegenLayoutPlan


__all__: tuple[str, ...] = (
    "FlextInfraCodegenLayoutApply",
    "FlextInfraCodegenLayoutFiles",
    "FlextInfraCodegenLayoutGitignore",
    "FlextInfraCodegenLayoutPlan",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegenLayoutApply": ".apply",
        "FlextInfraCodegenLayoutFiles": ".files",
        "FlextInfraCodegenLayoutGitignore": ".ignore",
        "FlextInfraCodegenLayoutPlan": ".plan",
    }),
    public_exports=__all__,
)
