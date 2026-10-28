"""Buildable models: deferred builds resolve once the module is complete.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from typing import Annotated

from flext_core import m


class FixtureModels:
    """Family whose members name a sibling through the family itself."""

    class Child(m.ContractModel):
        """Referenced sibling."""

        label: Annotated[str, m.Field(description="Label.")]

    class Entry(m.ContractModel):
        """Member naming its sibling through the family, built on first use."""

        child: Annotated[
            FixtureModels.Child,
            m.Field(description="Sibling named through the family."),
        ]


__all__: list[str] = ["FixtureModels"]
