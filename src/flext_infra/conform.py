"""Extracted facade class for conform.

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

from flext_infra._conform import FlextInfraConformWiring


class FlextInfraFlextInfraConform(
    FlextInfraConformWiring,
):
    """Facade for conform."""


__all__: list[str] = ["FlextInfraFlextInfraConform"]
