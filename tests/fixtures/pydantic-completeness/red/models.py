"""Unbuildable model: a field type exists only for type checking.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from flext_core import m

if TYPE_CHECKING:
    from decimal import Decimal


class FixtureModels:
    """Family whose member names a type imported only for type checking."""

    class Ledger(m.ContractModel):
        """Its field type is never bound at runtime, so it never builds."""

        amount: Annotated[Decimal, m.Field(description="Amount.")]


__all__: list[str] = ["FixtureModels"]
