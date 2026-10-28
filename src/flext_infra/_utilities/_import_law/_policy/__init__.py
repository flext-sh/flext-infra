# AUTO-GENERATED FILE — Regenerate with: make gen
"""policy package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._policy.namespace import (
        FlextInfraUtilitiesImportLawPolicyNamespace,
    )
    from flext_infra._policy.publication import (
        FlextInfraUtilitiesImportLawPolicyPublication,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesImportLawPolicyNamespace",
    "FlextInfraUtilitiesImportLawPolicyPublication",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesImportLawPolicyNamespace": ".namespace",
        "FlextInfraUtilitiesImportLawPolicyPublication": ".publication",
    }),
    public_exports=__all__,
)
