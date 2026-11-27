# AUTO-GENERATED FILE — Regenerate with: make check
"""Flext Infra. Utilities. Protocol Models package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._protocol_models.bootstrap_admission import (
        FlextInfraUtilitiesModelsProtocolBootstrapAdmission,
    )
    from flext_infra._utilities._protocol_models.bootstrap_package import (
        FlextInfraUtilitiesModelsProtocolBootstrapPackage,
    )
    from flext_infra._utilities._protocol_models.bootstrap_sources import (
        FlextInfraUtilitiesModelsProtocolBootstrapSources,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesModelsProtocolBootstrapAdmission",
    "FlextInfraUtilitiesModelsProtocolBootstrapPackage",
    "FlextInfraUtilitiesModelsProtocolBootstrapSources",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesModelsProtocolBootstrapAdmission": ".bootstrap_admission",
        "FlextInfraUtilitiesModelsProtocolBootstrapPackage": ".bootstrap_package",
        "FlextInfraUtilitiesModelsProtocolBootstrapSources": ".bootstrap_sources",
    },
    public_exports=__all__,
)
