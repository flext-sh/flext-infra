"""Bootstrap-safe selection from the declared Make operation contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraMakeContract:
    """Elect operation names without importing configuration or model facades."""

    @staticmethod
    def selector_free_make_verbs(
        verbs: t.SequenceOf[p.Infra.MakeOperation],
        required_profiles: t.StrSequence,
    ) -> frozenset[str]:
        """Elect argument-free operations declared in every Make profile.

        Returns:
            Admissible names; callers retain their selection policy and errors.
        """
        profiles = frozenset(required_profiles)
        return frozenset(
            verb.name
            for verb in verbs
            if not verb.arguments and set(verb.profiles) == profiles
        )


__all__: list[str] = []
