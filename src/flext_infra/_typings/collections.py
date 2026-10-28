"""Collection-generic type aliases for flext-infra.

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

import collections.abc


class FlextInfraTypesCollections:
    """Infra collection-generic type aliases composed into ``t``."""

    type Container[T] = collections.abc.Container[T]


__all__: list[str] = ["FlextInfraTypesCollections"]
