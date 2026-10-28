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
    from flext_infra._codegen.base import FlextInfraCodegen
    from flext_infra._codegen.fix import FlextInfraModelsCodegenFix
    from flext_infra._codegen.lazy_init import FlextInfraModelsCodegenLazyInit
    from flext_infra._codegen.pipeline import FlextInfraModelsCodegenPipeline
    from flext_infra._codegen.scaffold import FlextInfraModelsCodegenScaffold
    from flext_infra._codegen.transaction import FlextInfraModelsCodegenTransaction


__all__: tuple[str, ...] = (
    "FlextInfraCodegen",
    "FlextInfraModelsCodegenFix",
    "FlextInfraModelsCodegenLazyInit",
    "FlextInfraModelsCodegenPipeline",
    "FlextInfraModelsCodegenScaffold",
    "FlextInfraModelsCodegenTransaction",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegen": ".base",
        "FlextInfraModelsCodegenFix": ".fix",
        "FlextInfraModelsCodegenLazyInit": ".lazy_init",
        "FlextInfraModelsCodegenPipeline": ".pipeline",
        "FlextInfraModelsCodegenScaffold": ".scaffold",
        "FlextInfraModelsCodegenTransaction": ".transaction",
    }),
    public_exports=__all__,
)
