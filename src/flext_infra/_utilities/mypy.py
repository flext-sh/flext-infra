"""Extracted facade class for mypy.

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

from flext_infra._utilities._mypy import (
    FlextInfraUtilitiesMypyProfile,
    FlextInfraUtilitiesMypySupervisor,
)


class FlextInfraUtilitiesMypy(
    FlextInfraUtilitiesMypyProfile,
    FlextInfraUtilitiesMypySupervisor,
):
    """Facade for mypy."""


__all__: list[str] = ["FlextInfraUtilitiesMypy"]
