"""Capability base a stand-in cannot represent: an isinstance against its own class.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations


class FlextDemoCapabilityBase:
    """Members a deferred subclass inherits from its package."""

    def base_is_self(self) -> bool:
        """Return whether the instance is the real part class.

        Returns:
            Whether it is.

        """
        return isinstance(self, FlextDemoCapabilityBase)

    @staticmethod
    def base_value() -> int:
        """Return the value the base declares.

        Returns:
            The base value.

        """
        return 1


__all__: list[str] = ["FlextDemoCapabilityBase"]
