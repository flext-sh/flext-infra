"""Capability whose module imports a deferred distribution at module scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

import requests
from requests import Session

from flext_demo._capability import FlextDemoCapabilityBase


class FlextDemoCapabilityHeavy(FlextDemoCapabilityBase):
    """Members the generated initializer defers to their first access."""

    TIMEOUT_ERROR: ClassVar[type[Exception]] = requests.Timeout

    @staticmethod
    def heavy_value() -> int:
        """Return the value only the heavy capability declares.

        Returns:
            The heavy value.

        """
        return 2


class FlextDemoCapabilityClient(Session):
    """Instantiated class with a third-party base: never composed into a facade."""


__all__: list[str] = ["FlextDemoCapabilityClient", "FlextDemoCapabilityHeavy"]
