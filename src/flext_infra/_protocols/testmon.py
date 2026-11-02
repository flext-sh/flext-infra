# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/testmon
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


class FlextInfraProtocolsTestmon:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class TestmonCacheState(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def seed_needed(self) -> bool: ...
        @property
        def restored_accepted(self) -> bool: ...
        @property
        def changed(self) -> bool: ...
        @property
        def saveable(self) -> bool: ...
        @property
        def reason(self) -> str: ...

    @runtime_checkable
    class TestmonCachePublication(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def database(self) -> Path: ...
        @property
        def digest(self) -> str: ...
        @property
        def saveable(self) -> bool: ...

    @runtime_checkable
    class TestmonRunAccounting(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def executed_count(self) -> int: ...
        @property
        def reported_count(self) -> int: ...
        @property
        def deselected_count(self) -> int: ...
        @property
        def inventory_count(self) -> int | None: ...
        @property
        def cache_restored(self) -> bool: ...
        @property
        def owns_no_tests(self) -> bool: ...


__all__: list[str] = [
    "FlextInfraProtocolsTestmon",
]
