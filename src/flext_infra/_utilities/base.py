"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping

from flext_infra import t


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    """

    @staticmethod
    def get_str_key(
        mapping: Mapping[str, t.Infra.InfraValue],
        key: str,
        *,
        default: str = "",
        lower: bool = False,
    ) -> str:
        """Extract and normalize a string key from a config mapping.

        Replaces the repeated ``str(mapping.get(key, "")).strip().lower()`` pattern.

        Args:
            mapping: Source mapping (e.g., rule config dict).
            key: Key to extract.
            default: Default value if key is missing.
            lower: If True, also lowercase the result.

        Returns:
            Stripped (and optionally lowercased) string value.

        """
        raw = str(mapping.get(key, default)).strip()
        return raw.lower() if lower else raw
