"""The same model with its thread declared through the port owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
import threading
from typing import Annotated

from flext_core import m, t


class FixtureArbitrary(m.ArbitraryTypesModel):
    """Holds a thread validated by ``isinstance`` through ``t.Port``."""

    worker: Annotated[
        t.Port[threading.Thread] | None,
        m.Field(description="Thread validated by its port."),
    ] = None


__all__: list[str] = ["FixtureArbitrary"]
