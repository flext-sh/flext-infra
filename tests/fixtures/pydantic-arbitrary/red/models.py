"""A model whose field only builds through ``arbitrary_types_allowed``.

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

from flext_core import m


class FixtureArbitrary(m.ArbitraryTypesModel):
    """Holds a thread the schema cannot describe."""

    worker: Annotated[
        threading.Thread | None,
        m.Field(description="Thread accepted only by the flag."),
    ] = None


__all__: list[str] = ["FixtureArbitrary"]
