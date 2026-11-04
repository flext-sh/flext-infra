# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
tests/_protocols/semantic_cutover
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import FlextInfraProtocols


class TestsFlextInfraProtocolsSemanticCutover:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SemanticCutoverScenario(FlextInfraProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def template(self) -> str:
            """J2 template name."""
            ...

        @property
        def module(self) -> str:
            """Imported module."""
            ...

        @property
        def names(self) -> str:
            """Imported names."""
            ...

        @property
        def alias(self) -> str:
            """Optional import alias."""
            ...

        @property
        def body(self) -> str:
            """Module body."""
            ...

        @property
        def header(self) -> str:
            """Module header."""
            ...

        @property
        def assertions(self) -> str:
            """Assert expressions, one per line."""
            ...

        @property
        def message(self) -> str:
            """Optional assert message."""
            ...


__all__: list[str] = [
    "TestsFlextInfraProtocolsSemanticCutover",
]
