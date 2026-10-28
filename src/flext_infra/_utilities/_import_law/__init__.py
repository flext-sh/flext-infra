# AUTO-GENERATED FILE — Regenerate with: make gen
"""import law package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._import_law._policy.namespace import (
        FlextInfraUtilitiesImportLawPolicyNamespace,
    )
    from flext_infra._import_law._policy.publication import (
        FlextInfraUtilitiesImportLawPolicyPublication,
    )
    from flext_infra._import_law.ast import FlextInfraUtilitiesImportLawAst
    from flext_infra._import_law.graph import FlextInfraUtilitiesImportLawGraph
    from flext_infra._import_law.normalization import (
        FlextInfraUtilitiesImportLawNormalization,
    )
    from flext_infra._import_law.placement import FlextInfraUtilitiesImportLawPlacement
    from flext_infra._import_law.policy import FlextInfraUtilitiesImportLawPolicy
    from flext_infra._import_law.routes import FlextInfraUtilitiesImportLawRoutes


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesImportLawAst",
    "FlextInfraUtilitiesImportLawGraph",
    "FlextInfraUtilitiesImportLawNormalization",
    "FlextInfraUtilitiesImportLawPlacement",
    "FlextInfraUtilitiesImportLawPolicy",
    "FlextInfraUtilitiesImportLawPolicyNamespace",
    "FlextInfraUtilitiesImportLawPolicyPublication",
    "FlextInfraUtilitiesImportLawRoutes",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesImportLawAst": ".ast",
        "FlextInfraUtilitiesImportLawGraph": ".graph",
        "FlextInfraUtilitiesImportLawNormalization": ".normalization",
        "FlextInfraUtilitiesImportLawPlacement": ".placement",
        "FlextInfraUtilitiesImportLawPolicy": ".policy",
        "FlextInfraUtilitiesImportLawPolicyNamespace": "._policy.namespace",
        "FlextInfraUtilitiesImportLawPolicyPublication": "._policy.publication",
        "FlextInfraUtilitiesImportLawRoutes": ".routes",
    }),
    public_exports=__all__,
)
