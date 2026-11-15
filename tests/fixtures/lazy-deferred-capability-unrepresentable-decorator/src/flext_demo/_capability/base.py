"""Capability base a stand-in cannot represent: a Pydantic field decorator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pydantic import computed_field


class FlextDemoCapabilityBase:
    """Members a deferred subclass inherits from its package."""

    @computed_field
    def base_total(self) -> int:
        """Return a computed field the stand-in would lose.

        Returns:
            The total.

        """
        return 3

    @staticmethod
    def base_value() -> int:
        """Return the value the base declares.

        Returns:
            The base value.

        """
        return 1


__all__: list[str] = ["FlextDemoCapabilityBase"]
