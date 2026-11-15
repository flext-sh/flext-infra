"""Capability base a stand-in cannot represent: a dunder method.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations


class FlextDemoCapabilityBase:
    """Members a deferred subclass inherits from its package."""

    def __repr__(self) -> str:
        """Return a representation the stand-in would lose.

        Returns:
            The representation.

        """
        return "base"

    @staticmethod
    def base_value() -> int:
        """Return the value the base declares.

        Returns:
            The base value.

        """
        return 1


__all__: list[str] = ["FlextDemoCapabilityBase"]
