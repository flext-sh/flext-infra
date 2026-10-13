"""Bootstrap-safe Make capability contract shared by config and runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence


class FlextInfraMakeContract:
    """Make admission behavior independent of project facades and configuration."""

    @staticmethod
    def selector_free_make_verb[Profile: str](
        arguments: Sequence[str],
        profiles: Sequence[Profile],
        required_profiles: Sequence[Profile],
    ) -> bool:
        """Check argument-free applicability against the declared profile universe.

        Returns:
            Whether the operation satisfies selector-free all-profile admission.
        """
        return not arguments and set(profiles) == set(required_profiles)


__all__: list[str] = []
