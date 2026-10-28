"""Extracted facade class for census.

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

from flext_infra.refactor._census import (
    FlextInfraRefactorCensusCollectHelpers,
    FlextInfraRefactorCensusRender,
)


class FlextInfraRefactorCensus(
    FlextInfraRefactorCensusCollectHelpers,
    FlextInfraRefactorCensusRender,
):
    """Facade for census."""


__all__: list[str] = ["FlextInfraRefactorCensus"]
