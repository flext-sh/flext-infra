"""Incomplete model: a field names a sibling through its unbound family class.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_core import m


class FixtureModels:
    """Family whose member names a sibling through the family itself."""

    class Entry(m.ContractModel):
        """Member left incomplete: the family is unbound at its creation."""

        child: Annotated[
            FixtureModels.Child,
            m.Field(description="Sibling named through the family."),
        ]

    class Child(m.ContractModel):
        """Referenced sibling."""

        label: Annotated[str, m.Field(description="Label.")]


__all__ = ["FixtureModels"]
