# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/enforcement_catalog
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._constants import FlextInfraConstantsCheck
    from flext_infra._typings import FlextInfraTypesBase


class FlextInfraProtocolsEnforcementCatalog:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class EnforcementClaim(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> FlextInfraTypesBase.EnforcementId:
            """Claimed enforcement law identity."""
            ...

        @property
        def engine(self) -> FlextInfraConstantsCheck.EnforcementEngine:
            """Engine whose declaration makes the claim."""
            ...

        @property
        def owner(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Claiming declaration inside the engine: ast-grep rule id, Ruff rule
            name, gate id or codegen template destination.
            """
            ...

        @property
        def code(self) -> t.NonEmptyStr | None:
            """Finding code the gate reports for the claim."""
            ...

        @property
        def active(self) -> bool:
            """Whether the claiming owner currently runs."""
            ...

    @runtime_checkable
    class EnforcementCatalog(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def claims(
            self,
        ) -> tuple[FlextInfraProtocolsEnforcementCatalog.EnforcementClaim, ...]:
            """Claims in owner declaration order."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsEnforcementCatalog",
]
