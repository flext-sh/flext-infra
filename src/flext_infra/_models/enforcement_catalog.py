"""Derived enforcement catalog contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import c, t


class FlextInfraModelsEnforcementCatalog:
    """Claims collected from the owners that detect enforcement laws."""

    class EnforcementClaim(m.FrozenModel):
        """One owner declaration claiming one enforcement law id."""

        id: Annotated[
            t.Infra.EnforcementId,
            m.Field(description="Claimed enforcement law identity"),
        ]
        engine: Annotated[
            c.Infra.EnforcementEngine,
            m.Field(description="Engine whose declaration makes the claim"),
        ]
        owner: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Claiming declaration inside the engine: ast-grep rule id, "
                    "Ruff rule name, gate id or codegen template destination"
                ),
            ),
        ]
        code: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Finding code the gate reports for the claim"),
        ] = None
        active: Annotated[
            bool,
            m.Field(description="Whether the claiming owner currently runs"),
        ]

    class EnforcementCatalog(m.FrozenModel):
        """Every enforcement claim derived from its owners."""

        claims: Annotated[
            tuple[FlextInfraModelsEnforcementCatalog.EnforcementClaim, ...],
            m.Field(min_length=1, description="Claims in owner declaration order"),
        ]


__all__: list[str] = ["FlextInfraModelsEnforcementCatalog"]
