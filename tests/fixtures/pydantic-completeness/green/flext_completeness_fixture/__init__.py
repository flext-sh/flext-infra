"""Complete model: the referenced type is bound before the family is created.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_core import m


class FixtureChild(m.ContractModel):
    """Referenced model, owned by its own declaration."""

    label: Annotated[str, m.Field(description="Label.")]


class FixtureModels:
    """Family whose member names an already bound model."""

    class Entry(m.ContractModel):
        """Member resolving its field at class creation."""

        child: Annotated[
            FixtureChild,
            m.Field(description="Model bound before the family."),
        ]


__all__ = ["FixtureChild", "FixtureModels"]
