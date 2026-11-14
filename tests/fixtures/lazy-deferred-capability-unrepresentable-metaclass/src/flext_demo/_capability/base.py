"""Capability base a stand-in cannot represent: a non-type metaclass.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from abc import ABCMeta


class FlextDemoCapabilityBase(metaclass=ABCMeta):
    """Members a deferred subclass inherits from its package."""

    @staticmethod
    def base_value() -> int:
        """Return the value the base declares.

        Returns:
            The base value.

        """
        return 1


__all__: list[str] = ["FlextDemoCapabilityBase"]
