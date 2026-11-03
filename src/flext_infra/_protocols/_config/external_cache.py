# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/external_cache
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract


class FlextInfraProtocolsConfigExternalCache:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class Directory[Environment: str = str](
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def data_home_environment_variable(self) -> Environment:
            """XDG persistent cache-home variable."""
            ...

        @property
        def user_home_environment_variable(self) -> Environment:
            """User home variable for the XDG default."""
            ...

        @property
        def home_cache_directory(self) -> Path:
            """Standard cache directory below the user home."""
            ...

        @property
        def external_storage_directory(self) -> Path:
            """FLEXT-owned directory below the cache home."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigExternalCache",
]
