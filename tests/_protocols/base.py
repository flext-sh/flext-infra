# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
tests/_protocols/base
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_tests import FlextTestsProtocols

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraProtocolsBase:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class AstGrepFixtureSnapshots(FlextTestsProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str:
            """Native rule identity."""
            ...

        @property
        def snapshots(self) -> Mapping[str, t.JsonMapping]:
            """Source cases and their native snapshot metadata."""
            ...

    @runtime_checkable
    class PytestDiagOptions(FlextTestsProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def failed(self) -> Path | None:
            """Failed cases output."""
            ...

        @property
        def errors(self) -> Path | None:
            """Error traces output."""
            ...

        @property
        def warnings(self) -> Path | None:
            """Warnings output."""
            ...

        @property
        def slowest(self) -> Path | None:
            """Slowest cases output."""
            ...

        @property
        def skips(self) -> Path | None:
            """Skipped cases output."""
            ...

        @property
        def events(self) -> str:
            """Native pytest report-log event stream."""
            ...

        @property
        def identities(self) -> str:
            """Native warning identities sidecar."""
            ...


__all__: list[str] = [
    "TestsFlextInfraProtocolsBase",
]
