# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/enforcement_catalog
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsEnforcementCatalog:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class EnforcementClaim(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.Infra.EnforcementId: ...
        @property
        def engine(self) -> c.Infra.EnforcementEngine: ...
        @property
        def owner(self) -> t.NonEmptyStr: ...
        @property
        def code(self) -> t.NonEmptyStr | None: ...
        @property
        def active(self) -> bool: ...

    @runtime_checkable
    class EnforcementCatalog(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def claims(self) -> tuple[p.Infra.EnforcementClaim, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsEnforcementCatalog",
]
