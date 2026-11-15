"""Capability base a stand-in cannot represent: a zero-argument super().

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations


class FlextDemoCapabilityBase:
    """Members a deferred subclass inherits from its package."""

    @classmethod
    def base_name(cls) -> str:
        """Return a name resolved through the real class's MRO.

        Returns:
            The name.

        """
        return super().__name__

    @staticmethod
    def base_value() -> int:
        """Return the value the base declares.

        Returns:
            The base value.

        """
        return 1


__all__: list[str] = ["FlextDemoCapabilityBase"]
