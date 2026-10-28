"""Extracted facade class for pytest.

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

from flext_infra._pytest import (
    FlextInfraPytestClock,
    FlextInfraPytestCollection,
    FlextInfraPytestEntry,
    FlextInfraPytestProfileChild,
)


class FlextInfraFlextInfraPytest(
    FlextInfraPytestClock,
    FlextInfraPytestCollection,
    FlextInfraPytestEntry,
    FlextInfraPytestProfileChild,
):
    """Facade for pytest."""


__all__: list[str] = ["FlextInfraFlextInfraPytest"]
