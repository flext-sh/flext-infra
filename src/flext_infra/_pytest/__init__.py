# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for pytest.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._pytest.clock import FlextInfraPytestClock
    from flext_infra._pytest.collection import FlextInfraPytestCollection
    from flext_infra._pytest.entry import FlextInfraPytestEntry
    from flext_infra._pytest.profile_child import FlextInfraPytestProfileChild

__all__: tuple[str, ...] = (
    "FlextInfraPytestClock",
    "FlextInfraPytestCollection",
    "FlextInfraPytestEntry",
    "FlextInfraPytestProfileChild",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraPytestClock": ".clock",
        "FlextInfraPytestCollection": ".collection",
        "FlextInfraPytestEntry": ".entry",
        "FlextInfraPytestProfileChild": ".profile_child",
    }),
    public_exports=__all__,
)
