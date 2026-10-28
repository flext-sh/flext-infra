"""Extracted facade class for project.

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

from flext_infra._utilities._project import (
    FlextInfraUtilitiesProjectDiscoveryCandidates,
)


class FlextInfraUtilitiesProject(
    FlextInfraUtilitiesProjectDiscoveryCandidates,
):
    """Facade for project."""


__all__: list[str] = ["FlextInfraUtilitiesProject"]
