# AUTO-GENERATED FILE — Regenerate with: make gen
"""pytest package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.validate._pytest.diag_xml import FlextInfraValidatePytestDiagXml


__all__: tuple[str, ...] = ("FlextInfraValidatePytestDiagXml",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraValidatePytestDiagXml": ".diag_xml",
    }),
    public_exports=__all__,
)
