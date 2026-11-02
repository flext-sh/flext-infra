# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/external_cache
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


class FlextInfraProtocolsConfigExternalCache:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class Directory[Environment: str = str](Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def data_home_environment_variable(self) -> Environment: ...
        @property
        def user_home_environment_variable(self) -> Environment: ...
        @property
        def home_cache_directory(self) -> Path: ...
        @property
        def external_storage_directory(self) -> Path: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigExternalCache",
]
