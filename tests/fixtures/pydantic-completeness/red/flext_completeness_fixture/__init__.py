"""Incomplete models: two root causes and one dependent.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from flext_core import m

if TYPE_CHECKING:
    from decimal import Decimal


class FixtureModels:
    """Family whose member names a sibling through the family itself."""

    class Entry(m.ContractModel):
        """Root cause: the family is unbound at the member's creation."""

        child: Annotated[
            FixtureModels.Child,
            m.Field(description="Sibling named through the family."),
        ]

    class Child(m.ContractModel):
        """Referenced sibling."""

        label: Annotated[str, m.Field(description="Label.")]


class FixtureLedger(m.ContractModel):
    """Root cause: its field type is imported only for type checking."""

    amount: Annotated[Decimal, m.Field(description="Amount.")]


class FixtureHolder(m.ContractModel):
    """Dependent: its field resolves to the incomplete ledger."""

    ledger: Annotated[
        FixtureLedger,
        m.Field(description="Incomplete model this model depends on."),
    ]


__all__ = ["FixtureHolder", "FixtureLedger", "FixtureModels"]
