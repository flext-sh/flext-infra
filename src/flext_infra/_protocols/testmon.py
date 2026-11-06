# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/testmon
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols


class FlextInfraProtocolsTestmon:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class TestmonCacheState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def seed_needed(self) -> bool:
            """No usable DB was present."""
            ...

        @property
        def restored_accepted(self) -> bool:
            """An existing DB passed integrity checks."""
            ...

        @property
        def changed(self) -> bool:
            """DB content changed relative to its input digest."""
            ...

        @property
        def saveable(self) -> bool:
            """DB may be published as a cache generation."""
            ...

        @property
        def reason(self) -> str:
            """Decisive cache-state reason."""
            ...

    @runtime_checkable
    class TestmonCachePublication(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def database(self) -> Path:
            """Integrity-checked project database."""
            ...

        @property
        def digest(self) -> str:
            """Checkpoint digest."""
            ...

        @property
        def saveable(self) -> bool:
            """Completed run may publish this generation."""
            ...

    @runtime_checkable
    class TestmonRunAccounting(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def executed_count(self) -> int:
            """JUnit testcase count."""
            ...

        @property
        def reported_count(self) -> int:
            """Unique node IDs with real TestReport events."""
            ...

        @property
        def deselected_count(self) -> int:
            """Complete inventory minus the canonical selected node IDs."""
            ...

        @property
        def inventory_count(self) -> int | None:
            """Structural member projected from the owning model.

            Complete testmon inventory; absent for coverage; zero only when the
            project owns no test module (owns_no_tests receipt).
            """
            ...

        @property
        def cache_restored(self) -> bool:
            """Input database passed SQLite integrity checks."""
            ...

        @property
        def owns_no_tests(self) -> bool:
            """Structural member projected from the owning model.

            The project declares no test module under the config-owned collection
            roots: zero execution by declared design.
            """
            ...


__all__: list[str] = [
    "FlextInfraProtocolsTestmon",
]
