# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/refactor_namespace_enforcer
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsRefactorNamespaceEnforcer:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ParseFailureViolation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def detail(self) -> str:
            """Error detail."""
            ...

        @property
        def file(self) -> t.NonEmptyStr:
            """File path."""
            ...

        @property
        def stage(self) -> t.NonEmptyStr:
            """Parse stage."""
            ...

        @property
        def error_type(self) -> t.NonEmptyStr:
            """Error type."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsRefactorNamespaceEnforcer",
]
