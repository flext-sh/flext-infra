"""Bootstrap-safe Make capability contract shared by config and runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence


class FlextInfraConfigMakeContract:
    """Make admission behavior independent of project facades and configuration."""

    @staticmethod
    def make_verb_supports_profiles[Profile: str](
        profiles: Sequence[Profile],
        required_profiles: Sequence[Profile],
    ) -> bool:
        """Check applicability against the declared profile universe.

        Help metadata describes optional data inputs, not partial execution.
        The generated common handlers own their complete operation scope.

        Returns:
            Whether the operation is available in every required profile.

        """
        return set(profiles) == set(required_profiles)


__all__: list[str] = []
