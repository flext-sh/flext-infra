# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Import Law package.

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
    from flext_infra._utilities._import_law.ast import FlextInfraUtilitiesImportLawAst
    from flext_infra._utilities._import_law.graph import (
        FlextInfraUtilitiesImportLawGraph,
    )
    from flext_infra._utilities._import_law.normalization import (
        FlextInfraUtilitiesImportLawNormalization,
    )
    from flext_infra._utilities._import_law.placement import (
        FlextInfraUtilitiesImportLawPlacement,
    )
    from flext_infra._utilities._import_law.policy import (
        FlextInfraUtilitiesImportLawPolicy,
    )
    from flext_infra._utilities._import_law.routes import (
        FlextInfraUtilitiesImportLawRoutes,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesImportLawAst",
    "FlextInfraUtilitiesImportLawGraph",
    "FlextInfraUtilitiesImportLawNormalization",
    "FlextInfraUtilitiesImportLawPlacement",
    "FlextInfraUtilitiesImportLawPolicy",
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
        "FlextInfraUtilitiesImportLawRoutes": ".routes",
    }),
    public_exports=__all__,
)
