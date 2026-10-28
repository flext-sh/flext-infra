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
    from flext_infra._codegen.fix import FlextInfraModelsModelsCodegenFix
    from flext_infra._codegen.lazy_init import FlextInfraModelsModelsCodegenLazyInit
    from flext_infra._codegen.pipeline import FlextInfraModelsModelsCodegenPipeline
    from flext_infra._codegen.scaffold import FlextInfraModelsModelsCodegenScaffold
    from flext_infra._codegen.transaction import (
        FlextInfraModelsModelsCodegenTransaction,
    )


__all__: tuple[str, ...] = (
    "FlextInfraCodegen",
    "FlextInfraModelsModelsCodegenFix",
    "FlextInfraModelsModelsCodegenLazyInit",
    "FlextInfraModelsModelsCodegenPipeline",
    "FlextInfraModelsModelsCodegenScaffold",
    "FlextInfraModelsModelsCodegenTransaction",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegen": ".base",
        "FlextInfraModelsModelsCodegenFix": ".fix",
        "FlextInfraModelsModelsCodegenLazyInit": ".lazy_init",
        "FlextInfraModelsModelsCodegenPipeline": ".pipeline",
        "FlextInfraModelsModelsCodegenScaffold": ".scaffold",
        "FlextInfraModelsModelsCodegenTransaction": ".transaction",
    }),
    public_exports=__all__,
)
